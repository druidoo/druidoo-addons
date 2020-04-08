from collections import defaultdict

from odoo import fields, models
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    pos_order_id = fields.One2many(
        'pos.order',
        'invoice_id',
        string='POS Order',
        ondelete='set null',
        readonly=True,
    )

    def _get_invoiced_lot_values(self):
        """ Get and prepare data to show a table of invoiced lot
        from POS Orders on the invoice's report. """
        self.ensure_one()

        if self.state == 'draft':
            return []

        if not self.pos_order_id:
            return super()._get_invoiced_lot_values()

        stock_move_lines = self.pos_order_id.mapped(
            'picking_id.move_lines.move_line_ids')

        def _filter_incoming_sml(ml):
            return (
                ml.state == 'done'
                and ml.location_id.usage == 'customer'
                and ml.lot_id
            )

        def _filter_outgoing_sml(ml):
            return (
                ml.state == 'done'
                and ml.location_dest_id.usage == 'customer'
                and ml.lot_id:
            )

        incoming_sml = stock_move_lines.filtered(_filter_incoming_sml)
        outgoing_sml = stock_move_lines.filtered(_filter_outgoing_sml)

        # Prepare and return lot_values
        qty_per_lot = defaultdict(lambda: 0)
        if self.type == 'out_refund':
            for ml in outgoing_sml:
                qty_per_lot[ml.lot_id] -= ml.product_uom_id._compute_quantity(
                        ml.qty_done, ml.product_id.uom_id)
            for ml in incoming_sml:
                qty_per_lot[ml.lot_id] += ml.product_uom_id._compute_quantity(
                        ml.qty_done, ml.product_id.uom_id)
        else:
            for ml in outgoing_sml:
                qty_per_lot[ml.lot_id] += ml.product_uom_id._compute_quantity(
                        ml.qty_done, ml.product_id.uom_id)
            for ml in incoming_sml:
                qty_per_lot[ml.lot_id] -= ml.product_uom_id._compute_quantity(
                        ml.qty_done, ml.product_id.uom_id)
        lot_values = []
        for lot_id, qty in qty_per_lot.items():
            if float_is_zero(
                    qty, precision_rounding=lot_id.product_id.uom_id.rounding
            ):
                continue
            lot_values.append({
                'product_name': lot_id.product_id.name,
                'quantity': qty,
                'uom_name': lot_id.product_uom_id.name,
                'lot_name': lot_id.name,
            })
        return lot_values
