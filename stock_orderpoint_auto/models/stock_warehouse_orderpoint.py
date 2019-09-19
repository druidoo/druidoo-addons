# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError
from datetime import datetime 
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    orderpoint_type = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
        ],
        string='Type',
        help='If automatic, min and max quantities will be calculated '
             'using move history from the last months.',
        default='manual',
        required=True,
    )

    auto_min_months = fields.Float('Minimum stock in months', default=1)
    auto_max_months = fields.Float('Maximum stock in months', default=2)
    
    auto_analyze_months = fields.Integer(
        'Months to analyze',
        help='Number of months to analyze history. '
             'The min and max values will be calculated based on '
             'the average outgoing quantities of those months.',
        default=3,
    )

    @api.multi
    def _get_outgoing_moves_domain(self):
        self.ensure_one()
        return [
            ('state', '=', 'done'),
            ('product_id', '=', self.product_id.id),
            ('location_id', 'child_of', self.location_id.id),
        ]

    @api.multi
    def compute_orderpoint_auto(self):
        """ Get's history movements of this product and calculate
        the minimum and maximum quantities based on them.
        """
        self = self.filtered(lambda r: r.orderpoint_type == 'auto')
        for rec in self:
            # Get statistics
            from_date = \
                datetime.now() + relativedelta(months=-rec.auto_analyze_months)
            domain = rec._get_outgoing_moves_domain()
            domain.append(('date', '>=', from_date.strftime('%Y-%m-%d')))
            
            data = self.env['stock.move'].read_group(
                rec._get_outgoing_moves_domain(),
                fields=['product_qty'],
                groupby='product_id')

            if not data:
                raise UserError(_(
                    'There\'re no outgoing moves for this product in '
                    'this location.\n'
                    'Please use manual orderpoints until you have enough '
                    'data to analyze.'))
                
            qty = data[0].get('product_qty', 0.00)
            qty_per_month = qty / rec.auto_analyze_months

            rec.product_min_qty = tools.float_round(
                qty_per_month * rec.auto_min_months,
                precision_rounding=rec.product_id.uom_id.rounding,
                rounding_method='UP')

            rec.product_max_qty = tools.float_round(
                qty_per_month * rec.auto_max_months,
                precision_rounding=rec.product_id.uom_id.rounding,
                rounding_method='UP')

    @api.multi
    @api.constrains('orderpoint_type', 'auto_analyze_months')
    def _check_auto_analyze_months(self):
        for rec in self.filtered(lambda r: r.orderpoint_type == 'auto'):
            if rec.auto_analyze_months < 1:
                raise UserError(_(
                    'When using automatic reordering computation, '
                    'months to analyze should be bigger or equal to 1.\n'
                    'It\'s recommended that you analize at least 3 months.'))

    @api.multi
    @api.constrains(
        'orderpoint_type', 'product_id', 'location_id',
        'auto_analyze_months', 'auto_min_months', 'auto_max_months')
    def _compute_orderpoint_auto(self):
        """ We use constrains to trigger it only when record is saved """
        self.compute_orderpoint_auto()

    @api.model
    def _cron_compute_orderpoint_auto(self):
        records = self.search([('orderpoint_type', '=', 'auto')])
        records.compute_orderpoint_auto()
