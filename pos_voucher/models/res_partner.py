from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    voucher_count = fields.Integer(compute='_compute_voucher_count')

    def _compute_voucher_count(self):
        voucher_obj = self.env['pos.voucher']
        for rec in self:
            rec.voucher_count = voucher_obj.search(
                [('state', 'in', ('validated', 'partially_consumed')),
                 ('partner_id', '=', rec.id)
                 ], count=True)

    @api.multi
    def action_view_vouchers(self):
        self.ensure_one()
        action = self.env.ref('pos_voucher.act_pos_voucher').read()[0]
        action['context'] = {'search_default_filter_validated': 1,
                             'search_default_filter_partially_consumed': 1,
                             'search_default_partner_id': self.id}
        return action
