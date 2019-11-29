
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import Warning


class PosVoucherType(models.Model):
    _name = 'pos.voucher.type'
    _description = 'POS Voucher Type'

    name = fields.Char('Type', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True,
                                 domain="[('is_voucher', '=', True)]")
    sequence_id = fields.Many2one('ir.sequence', required=True)


class POSVoucher(models.Model):
    _name = 'pos.voucher'
    _inherit = ['mail.thread']
    _rec_name = 'code'
    _description = 'POS Voucher'

    code = fields.Char(required=True, default='/', copy=False)
    start_date = fields.Datetime(required=True)
    end_date = fields.Datetime()
    type_id = fields.Many2one('pos.voucher.type', 'Type', required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    consume_date = fields.Datetime('Consumed on',
                                   compute='_compute_date_amount', store=True)
    discount_type = fields.Selection([('fixed', 'Fixed')], default='fixed')
    total_amount = fields.Monetary()
    pending_amount = fields.Monetary(compute='_compute_date_amount',
                                     store=True)
    history_ids = fields.One2many('pos.voucher.history',
                                  'pos_voucher_id',
                                  'Voucher History')
    state = fields.Selection([('draft', 'Draft'),
                              ('validated', 'Validated'),
                              ('partially_consumed', 'Partially Consumed'),
                              ('consumed', 'Consumed'),
                              ('expired', 'Expired'),
                              ('cancelled', 'Cancelled')], default='draft',
                             required=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self:
                                 self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string='Account Currency',
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id)

    _sql_constraints = [
        ('unique_code', 'unique (code)',
         'The Code of the Voucher must be unique!'),
        ('check_pending_amount', 'check(pending_amount>=0)',
         'Can not Apply more than allowed Amount!')
    ]

    @api.depends('total_amount', 'history_ids',
                 'history_ids.amount',
                 'history_ids.consumed_date')
    def _compute_date_amount(self):
        # TODO: Use read_group to improve performance
        for rec in self:
            consumed_amount = sum(rec.history_ids.mapped('amount'))
            rec.pending_amount = rec.total_amount - consumed_amount
            if rec.history_ids:
                consume_date = max(rec.history_ids.mapped('consumed_date'))
                rec.consume_date = consume_date

    @api.multi
    def action_validate(self):
        states = list(set(self.mapped('state')))
        if len(states) > 1 or states[0] != 'draft':
            raise Warning(_('All selected records has to be in Draft State!'))
        for rec in self:
            vals = {'state': 'validated'}
            if not rec.code or rec.code == '/':
                code = rec.type_id.sequence_id.next_by_code(
                    rec.type_id.sequence_id.code)
                vals.update({'code': code})
            rec.write(vals)
        return True

    @api.multi
    def action_consume(self):
        self.ensure_one()
        if self.pending_amount > 0:
            state = 'partially_consumed'
        else:
            state = 'consumed'
        return self.write({'state': state})

    @api.multi
    def action_force_expired(self):
        self.write({'state': 'expired', 'end_date': fields.Datetime.today()})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True

    @api.multi
    def action_draft(self):
        self.ensure_one()
        if self.history_ids:
            raise Warning(_('Can not set to Draft as Consume History is '
                            'created for the voucher!'))
        self.write({'state': 'draft'})
        return True

    @api.model
    def get_voucher_by_code(self, code, partner_id):
        if not code or not partner_id:
            return -1, 'Customer is not set!'
        voucher = self.env['pos.voucher'].search(
            [('code', '=', code), ('partner_id', '=', partner_id)], limit=1)
        if not voucher:
            return -1, "Voucher code with the customer dosn't exist!"
        else:
            if voucher.state in ('validated', 'partially_consumed'):
                return 1, voucher.read([])[0]
            else:
                return -1, 'Voucher is %s!' % str(voucher.state).title()


class POSVoucherHistory(models.Model):
    _name = 'pos.voucher.history'
    _description = 'POS Voucher History'

    pos_voucher_id = fields.Many2one('pos.voucher', 'Voucher', required=True,
                                     ondelete='cascade')
    consumed_date = fields.Datetime(required=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(related='pos_voucher_id.currency_id',
                                  comodel_relation='res.currency',
                                  string='Account Currency')

    @api.model
    def create(self, vals):
        history = super().create(vals)
        history.pos_voucher_id.action_consume()
        return history


class PosOrder(models.Model):
    _inherit = "pos.order"

    voucher_history_id = fields.Many2one('pos.voucher.history', 'Voucher Used')

    @api.model
    def create_from_ui(self, orders):
        pos_voucher_obj = self.env['pos.voucher']
        voucher_history_obj = self.env['pos.voucher.history']
        for order in orders:
            order_data = order['data']
            if order_data.get('voucher_id'):
                voucher = pos_voucher_obj.browse(order_data.get('voucher_id'))
                statements = order_data['statement_ids']
                for statement_list in statements:
                    stmt = statement_list[2]
                    if stmt['journal_id'] == voucher.type_id.journal_id.id:
                        history = voucher_history_obj.create(
                            {
                             'pos_voucher_id': order_data.get('voucher_id'),
                             'consumed_date': stmt['name'],
                             'amount': stmt['amount'],
                             })
                        order_data['voucher_history_id'] = history.id
                        break

        return super().create_from_ui(orders)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_voucher = fields.Boolean('Use as a Voucher', default=False)

    @api.onchange('journal_user', 'type')
    def onchange_journal_user_type(self):
        self.is_voucher = False


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    is_voucher = fields.Boolean(related='journal_id.is_voucher', store=True)
