from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_lot_on_invoice = fields.Boolean(
        "Display Lots & Serial Numbers on Invoices",
        help="Lots & Serial numbers will appear on the invoice",
        implied_group='account_invoice_report_stock_lot.group_lot_on_invoice'
    )

    @api.onchange('group_stock_production_lot')
    def _onchange_group_stock_production_lot(self):
        if not self.group_stock_production_lot:
            self.group_lot_on_invoice = False
        return super()._onchange_group_stock_production_lot()
