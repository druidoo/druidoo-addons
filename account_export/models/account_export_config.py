from odoo import api, models, fields
from odoo.tools import safe_eval


class AccountExportConfig(models.Model):
    _name = "account.export.config"
    _description = "Account Export Config"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    is_default = fields.Boolean()

    credit_debit_format = fields.Selection([
        ('01', 'Debit: 0; Credit: 1'),
        ('DC', 'Debit: D; Credit: C'),
        ('-+', 'Debit: (+); Credit: (-)'),
        ('+-', 'Debit: (-); Credit: (+)'),
        ],
        string='Credit and Debit',
        default='01',
        required=True,
    )

    @api.model
    def _default_field_ids(self):
        vals = [
            'export_code', 'move_line_date', 'move_number',
            'export_account_code', 'account_move_name', 'amount',
        ]
        columns = self._get_columns_dict()
        return [
            (0, 0, {
                'sequence': (i+1)*10,
                'field_type': v,
                'name': columns.get(v, {}).get('name'),
            }) for i, v in enumerate(vals)]

    field_ids = fields.One2many(
        'account.export.config.field',
        'config_id',
        string='Fields',
        default=_default_field_ids,
    )

    @api.model
    def _get_columns_dict(self):
        """ Extend this method to add new column types """
        return {
            'export_code': {
                'name': 'Journal Export Code',
                'type': 'string',
            },
            'move_line_date': {
                'name': 'Move Line Date',
                'type': 'datetime',
            },
            'move_number': {
                'name': 'Move Number',
                'type': 'string',
            },
            'export_account_code': {
                'name': 'Account Export Code',
                'type': 'string',
            },
            'account_move_name': {
                'name': 'Move Name',
                'type': 'string',
            },
            'account_name': {
                'name': 'Account Name',
                'type': 'string',
            },
            'partner_ref': {
                'name': 'Partner Reference',
                'type': 'string',
            },
            'partner_name': {
                'name': 'Partner Name',
                'type': 'string',
                'width': 28,
            },
            'product_code': {
                'name': 'Product Code',
                'type': 'string',
            },
            'move_line_name': {
                'name': 'Move Line Name',
                'type': 'string',
            },
            'amount': {
                'name': 'Amount',
                'type': 'number',
            },
            'debit': {
                'name': 'Debit',
                'type': 'number',
            },
            'credit': {
                'name': 'Credit',
                'type': 'number',
            },
        }


class AccountExportConfigField(models.Model):
    _name = 'account.export.config.field'
    _description = 'Account Export Config Field'
    _order = 'config_id, sequence, name'

    @api.model
    def _get_field_type_selection(self):
        columns = self.config_id._get_columns_dict()
        return [(k, i.get('name')) for k, i in columns.items()]

    sequence = fields.Integer(default=10, required=True)

    name = fields.Char(
        help='The name of the field that\'s '
             'going to be used in the header',
        required=True,
    )

    description = fields.Char()

    config_id = fields.Many2one(
        'account.export.config',
        required=True,
        ondelete='cascade',
    )

    field_type = fields.Selection(
        selection=_get_field_type_selection,
        required=True,
        ondelete='cascade',
    )

    transform_expr = fields.Char(
        help='A python expression to transform the value.\n'
             'ie: value[:10]',
    )

    @api.multi
    def get_column_values(self, vals):
        """ Returns the column(s) value(s) from the values dict """
        res = {}
        for rec in self:
            if rec.field_type == 'amount':
                # TODO: Clean this.. it's ugly because of csv -> xls imp
                amount_vals = rec._get_columns_value_amount(vals)
                if rec.config_id.credit_debit_format in ('01', 'DC'):
                    res['%g_sense' % rec.id] = amount_vals[0]
                    res[rec.id] = amount_vals[1]
                else:
                    res[rec.id] = amount_vals[0]
            elif rec.transform_expr:
                try:
                    val = safe_eval(rec.transform_expr, {
                        'value': vals.get(rec.field_type),
                        'vals': vals,
                    })
                except Exception as e:
                    val = repr(e)
                res[rec.id] = val
            else:
                res[rec.id] = vals.get(rec.field_type)
        return res

    def _get_columns_value_amount(self, vals):
        # Format credit/debit based on format
        self.ensure_one()
        res = []
        credit_debit_format = self.config_id.credit_debit_format
        credit = vals.get('credit', 0)
        debit = vals.get('debit', 0)
        sense = None

        if debit > credit:
            if credit_debit_format == '01':
                sense = '0'
            elif credit_debit_format == 'DC':
                sense = 'D'
            amount = debit - credit
        else:
            if credit_debit_format == '01':
                sense = '1'
            elif credit_debit_format == 'DC':
                sense = 'C'
            amount = credit - debit

        # Signed credit/debit formats
        if credit_debit_format == '+-' and debit > credit:
            amount = -amount
        elif credit_debit_format == '-+' and debit <= credit:
            amount = -amount

        if credit_debit_format in ('01', 'DC'):
            res.append(sense)
        res.append(amount)
        return res
