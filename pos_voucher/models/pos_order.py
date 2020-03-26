from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = "pos.order"

    voucher_history_id = fields.Many2one(
        'pos.voucher.history',
        'Voucher Used',
    )

    @api.multi
    def _create_pos_vouchers(self):
        for order in self:
            for line in order.lines.filtered('voucher_type_id'):
                code = line.pos_voucher_code
                if not code:
                    raise ValidationError(_(
                        'Trying to create a voucher but the code is missing'))
                voucher_vals = {
                    'code': code,
                    'start_date': order.date_order,
                    'type_id': line.voucher_type_id.id,
                    'total_amount': line.price_subtotal_incl,
                    'company_id': line.company_id.id,
                    'pos_order_line_id': line.id,
                }
                if order.partner_id:
                    voucher_vals.update({
                        'partner_id': order.partner_id.id,
                    })
                pos_voucher_id = self.env['pos.voucher'].create(voucher_vals)
                line.pos_voucher_id = pos_voucher_id.id
                pos_voucher_id.action_validate()

    @api.model
    def create_from_ui(self, orders):
        voucher_history_obj = self.env['pos.voucher.history']
        for order in orders:
            order_data = order['data']
            if order_data.get('voucher_id'):
                statements = order_data['statement_ids']
                for statement_list in statements:
                    stmt = statement_list[2]
                    voucher = self.env['pos.voucher'].browse(stmt.get(
                        'voucher_id',
                        False
                    ))
                    if voucher:
                        history = voucher_history_obj.create({
                            'pos_voucher_id': voucher.id,
                            'consumed_date': stmt['name'],
                            'amount': stmt['amount'],
                        })
                        order_data['voucher_history_id'] = history.id
        # Generate vouchers
        order_ids = super().create_from_ui(orders)
        self.browse(order_ids)._create_pos_vouchers()
        return order_ids
