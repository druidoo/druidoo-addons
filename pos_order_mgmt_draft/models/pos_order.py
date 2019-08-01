# Copyright 2019 Druidoo - Iván Todorovich
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _name = 'pos.order'
    _inherit = ['pos.order', 'mail.thread']

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        ''' Add mail_post_autofollow to context '''
        return super(
            PosOrder,
            self.with_context(mail_post_autofollow=True)
        ).message_post(**kwargs)

    @api.model
    def _prepare_fields_for_pos_list(self):
        """ Add fields to order list data """
        res = super()._prepare_fields_for_pos_list()
        new_fields = ['state', 'id']
        for f in new_fields:
            if f not in res:
                res.append(f)
        return res

    @api.multi
    def _prepare_done_order_for_pos(self):
        """ Add fields to full order data """
        res = super()._prepare_done_order_for_pos()
        res['state'] = self.state
        return res

    @api.model
    def search_draft_orders_for_pos(self, query, pos_session_id):
        session_obj = self.env['pos.session']
        config = session_obj.browse(pos_session_id).config_id
        condition = [('state', '=', 'draft')]
        if not query:
            # Search only this POS orders
            condition += [('config_id', '=', config.id)]
        else:
            # Search globally by criteria
            condition += self._prepare_filter_query_for_pos(
                pos_session_id, query)
        field_names = self._prepare_fields_for_pos_list()
        return self.search_read(
            condition, field_names, limit=config.iface_load_done_order_max_qty)

    @api.model
    def create_from_ui(self, orders):
        """ Inherit method to handle continuing workflow of draft orders """
        draft_orders_to_process = [o for o in orders if o['data'].get('odoo_id')]
        orders = [o for o in orders if not o['data'].get('odoo_id')]
        order_ids = super().create_from_ui(orders)
        for tmp_order in draft_orders_to_process:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)
            pos_order = self._process_order(order)
            order_ids.append(pos_order.id)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.DatabaseError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                pos_order.action_pos_order_invoice()
                pos_order.invoice_id.sudo().with_context(force_company=self.env.user.company_id.id).action_invoice_open()
                pos_order.account_move = pos_order.invoice_id.move_id
        return order_ids

    @api.model
    def create_draft_from_ui(self, pos_order, options=None):
        """ Creates a draft order from the ui """
        if not options:
            options = {}
        odoo_id = pos_order.get('odoo_id')
        order = self.browse([odoo_id]).exists() if odoo_id else None
        vals = self._order_fields(pos_order)
        if order:
            if 'lines' in vals:
                vals['lines'] = [(5,0,0)] + (vals['lines'] or []);
            order.write(vals)
        else:
            order = self.create(vals)
        # Send mail if required
        if options.get('send_mail'):
            template_id = self.env.ref(
                'pos_order_mgmt_draft.email_template_pos_order')
            order.message_post_with_template(template_id.id)
        return order.id

    @api.model
    def _process_order(self, pos_order):
        """ Overload method to be able to create or modify orders
         WARNING: This doesn't handle payments at all.
         Draft orders should never have payments anyway..
        """
        pos_session = self.env['pos.session'].browse(pos_order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            pos_order['pos_session_id'] = self._get_valid_session(pos_order).id

        odoo_id = pos_order.get('odoo_id')
        order = self.browse([odoo_id]).exists() if odoo_id else None
        vals = self._order_fields(pos_order)
        if order:
            if 'lines' in vals:
                vals['lines'] = [(5,0,0)] + (vals['lines'] or []);
            order.write(vals)
        else:
            order = self.create(vals)

        prec_acc = order.pricelist_id.currency_id.decimal_places
        journal_ids = set()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                order.add_payment(self._payment_fields(payments[2]))
            journal_ids.add(payments[2]['journal_id'])

        if pos_session.sequence_number <= pos_order['sequence_number']:
            pos_session.write({'sequence_number': pos_order['sequence_number'] + 1})
            pos_session.refresh()

        if not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_journal_id = pos_session.cash_journal_id.id
            if not cash_journal_id:
                # Select for change one of the cash journals used in this
                # payment
                cash_journal = self.env['account.journal'].search([
                    ('type', '=', 'cash'),
                    ('id', 'in', list(journal_ids)),
                ], limit=1)
                if not cash_journal:
                    # If none, select for change one of the cash journals of the POS
                    # This is used for example when a customer pays by credit card
                    # an amount higher than total amount of the order and gets cash back
                    cash_journal = [statement.journal_id for statement in pos_session.statement_ids if statement.journal_id.type == 'cash']
                    if not cash_journal:
                        raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
                cash_journal_id = cash_journal[0].id
            order.add_payment({
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Date.context_today(self),
                'payment_name': _('return'),
                'journal': cash_journal_id,
            })
        return order
