# Copyright 2019 Druidoo (https://www.druidoo.io)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date
import base64


class AccountExport(models.Model):
    _name = "account.export"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        'Export filename',
        size=32,
        required=True,
        default=lambda self: self._get_default_name(),
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('exported', 'Exported')
        ],
        default='draft',
    )

    last_export_date = fields.Datetime(
        help='Last date of export',
        compute='_compute_last_export_date',
        readonly=True,
    )

    # Options
    filter_move_lines = fields.Selection([
        ('all', 'Export all move lines'),
        ('non_exported', 'Export only non exported move lines')
        ],
        'Move lines to export',
        default='non_exported',
    )

    # Filters
    date_from = fields.Date('From date')
    date_to = fields.Date('To date')

    invoice_ids = fields.Many2many(
        'account.invoice',
        string='Invoice',
        domain="[('company_id', '=', company_id)]",
    )

    journal_ids = fields.Many2many(
        'account.journal',
        string='Journals',
        domain="[('company_id', '=', company_id)]",
    )

    partner_ids = fields.Many2many('res.partner', string='Partner')

    config_id = fields.Many2one(
        'account.export.config',
        'Export Configuration',
        default=lambda self: self._get_default_config(),
        required=True,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help="Company related to this export",
        index=True,
        required=True,
        default=lambda self: self.env.user.company_id,
    )

    @api.constrains('company_id', 'journal_ids', 'invoice_ids')
    def _check_multi_company(self):
        for rec in self.filtered('company_id'):
            journal_company_ids = rec.journal_ids.mapped('company_id')
            invoice_company_ids = rec.invoice_ids.mapped('company_id')
            if journal_company_ids and journal_company_ids != rec.company_id:
                raise ValidationError(_(
                    'The company in the journals do not match the company '
                    'in this Export configuration. \n\n'
                    'Company on Journal: %s\n'
                    'Company on Export: %s') % (
                        journal_company_ids,
                        rec.company_id))
            if invoice_company_ids and invoice_company_ids != rec.company_id:
                raise ValidationError(_(
                    'The company in the invoices do not match the company '
                    'in this Export configuration. \n\n'
                    'Company on Invoices: %s\n'
                    'Company on Export: %s') % (
                        invoice_company_ids,
                        rec.company_id))

    # ############## MODEL FUNCTION FIELDS #####################

    @api.multi
    def _compute_last_export_date(self):
        self.ensure_one()
        ir_attachment_ids = self.env["ir.attachment"].search([
            ('res_model', '=', 'account.export'), ('res_id', '=', self.id)])
        if ir_attachment_ids:
            ir_attachment_ids.sorted(key=lambda v: v.write_date)
        self.last_export_date = ir_attachment_ids and\
            ir_attachment_ids[-1].write_date or False

    @api.model
    def _get_default_name(self):
        return "export%s" % date.today().strftime("%y%m%d")

    @api.model
    def _get_default_config(self):
        config = self.env['account.export.config'].search(
            [('is_default', '=', True)], limit=1)
        if not config:
            config = self.env['account.export.config'].search([], limit=1)
        return config and config.id or False

    # ################## EXPORTING FUNCTIONS ####################

    @api.multi
    def create_report(self):
        data, fileformat = self.env['ir.actions.report'].with_context(
            report_name='account_export.report_xls',
            active_model=self._name,
        ).render_xlsx(
            docids=self.ids,
            data={'dynamic_report': True},
        )
        # Attach file
        filename = '%s-%s.%s' % (
            self.name, fields.Datetime.now(), fileformat)
        # we use sudo() to workaround this issue:
        # https://github.com/odoo/odoo/issues/33543
        attach = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'res_id': self.id,
            'res_model': self._name,
            'datas': base64.encodestring(data),
            'datas_fname': filename,
        })
        # Open attachment view
        return {
            'name': self.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': attach.id,
        }

    # ############### MAIN FUNCTIONS TO GET DATA ###############

    @api.multi
    def get_account_move_line_data(self):
        '''
        @Function get the final data for exporting
        @Params:
        @Output: Final data for exporting to csv file
        '''
        self.ensure_one()

        # Get account move lines grouped by journal and related moves
        aml_groupedby_journal, move_ids = \
            self.get_account_move_line_group_by_journal()

        # Get header
        # output = self.HEADER and [self.HEADER] or []
        output = []

        for line in aml_groupedby_journal:
            journal_id = line['journal_id']
            move_line_ids = line['move_line_ids']
            groupings = self.get_journal_groupings(journal_id)

            # Get report line data
            line_data = \
                self.get_report_line_data(groupings, move_line_ids)
            output += line_data

        # Mark account move as exported
        self.env['account.move'].browse(move_ids).write({'exported': True})
        return output

    @api.model
    def get_report_line_data(self, groupings, move_line_ids):
        '''
        @Function to get the final data line
        '''
        res = []
        if groupings:
            # Finding the move lines which can be grouped together
            # pylint: disable=E8103
            sql_query = """
                SELECT {groupings}, array_agg(aml.id) as move_line_ids
                FROM account_move_line aml
                WHERE aml.id IN %s
                GROUP BY {groupings}
            """.format(groupings=', '.join(groupings))
            self.env.cr.execute(sql_query, (tuple(move_line_ids),))
            grouped_move_lines = self.env.cr.dictfetchall()

            for g_mv_line in grouped_move_lines:
                if not g_mv_line['move_line_ids']:
                    continue

                # Get the detail data
                report_line = self.get_report_line_detail_data(
                    g_mv_line['move_line_ids'], groupings)
                res.append(report_line)
        else:
            for acc_move_line in move_line_ids:
                # Get the detail data
                report_line = self.get_report_line_detail_data(
                    [acc_move_line], groupings=False)
                res.append(report_line)
        return res

    @api.model
    def get_report_line_detail_data(self, move_line_ids, groupings=False):
        '''
        @Function to get report data line in detail, according to the config
        @Params: move_line_ids: List of Move line ids. If Grouping = False, one
        element should be input.
                groupings: a líst of fields used for grouping move line
        '''
        vals = self._get_report_line_detail_data(move_line_ids, groupings)
        return self.config_id.field_ids.get_column_values(vals)

    @api.model
    def _get_report_line_detail_data(self, move_line_ids, groupings=False):
        '''
        @Function to get report data line in detail
        @Params: move_line_ids: List of Move line ids. If Grouping = False, one
        element should be input.
                groupings: a líst of fields used for grouping move line
        '''
        if not groupings:
            move_line_ids = move_line_ids[:1]
        sql_str = """
            SELECT
                aml.id,
                aj.id AS account_journal_id,
                (
                    CASE
                        WHEN aml.journal_id = NULL THEN 'NO-JOURNAL-CODE'
                    ELSE aj.export_code
                    END
                ) AS export_code,
                aj.code as journal_code,
                aml.partner_id AS partner_id,
                rp.name AS partner_name,
                aml.date,
                am.name AS move_number,
                (
                    CASE
                        WHEN (aml.partner_id IS NOT NULL)
                            AND (LEFT(aa.code, 3) = '401')
                            AND rp.property_account_payable_software
                                IS NOT NULL
                        THEN rp.property_account_payable_software

                        WHEN (aml.partner_id IS NOT NULL)
                            AND (LEFT(aa.code, 3) = '411')
                            AND rp.property_account_receivable_software
                                IS NOT NULL
                        THEN rp.property_account_receivable_software

                    ELSE COALESCE (aa.code, '')
                    END
                ) AS export_account_code,
                aa.code AS account_code,
                aa.name AS account_name,
                (
                    CASE WHEN aj.type = 'sale' THEN aml.ref
                        WHEN aj.type = 'purchase'
                        THEN COALESCE(rp.name, '')
                    ELSE
                        COALESCE (aml.ref, rp.name, '')
                    END
                ) AS account_move_name,

                aml.debit,
                aml.credit,

                COALESCE(aml.name,'') AS move_line_name,
                COALESCE(rp.ref,'') AS partner_ref,
                COALESCE(pt.name,'') AS product_name,
                COALESCE(pp.default_code,'') AS product_code

            FROM
                account_move_line aml
                LEFT JOIN account_journal aj ON aml.journal_id = aj.id
                LEFT JOIN account_move am ON aml.move_id = am.id
                LEFT JOIN res_partner rp ON aml.partner_id = rp.id
                LEFT JOIN account_account aa ON aml.account_id = aa.id
                LEFT JOIN product_product pp ON aml.product_id = pp.id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE aml.id IN %s
        """
        self._cr.execute(sql_str, (tuple(move_line_ids),))
        move_line_data = self._cr.dictfetchall()

        # Prepare response dict
        # As default, we send the values of the first line
        # Unless there are grouppings...
        res_data = dict(move_line_data[0])

        # Group the data of account move lines if groupings are set.
        # Otherwise, the result is the data of the first line
        if groupings:
            group_keys = [
                k for k in res_data.keys()
                if k not in ['credit', 'debit']
            ]
            res_data['debit'] = 0.0
            res_data['credit'] = 0.0
            for line in move_line_data:
                for key in group_keys:
                    if (
                        res_data[key]
                        and res_data[key] != "GROUPED"
                        and res_data[key] != line[key]
                    ):
                        res_data[key] = "GROUPED"
                res_data['debit'] += line['debit']
                res_data['credit'] += line['credit']

        # If export_code is missing, use journal code
        if not res_data.get('export_code') and res_data.get('journal_code'):
            res_data['export_code'] = res_data['journal_code']

        # Handle cases where the code is missing
        # (Legacy code)
        if res_data['export_code'] == 'NO-JOURNAL-CODE':
            res_data['export_code'] = None

        # Compatibility with old code
        res_data['move_line_date'] = res_data['date'] and str(res_data['date'])

        return res_data

    # ########### OTHER FUNCTIONS FOR GETTING DATA #############

    @api.multi
    def get_account_move_line_group_by_journal(self):
        '''
        @Function to get
            - account move line list grouped by journal
            - account move list involved
        '''
        # Building the Where Clause
        where_clause = 'WHERE am.state <> %s'
        where_params = ['draft']
        # Options
        if self.filter_move_lines == 'non_exported':
            where_clause += ' AND am.exported IS NOT TRUE'

        # Filters
        if self.date_from:
            where_clause += " AND aml.date >= %s"
            where_params.append(self.date_from)
        if self.date_to:
            where_clause += " AND aml.date <= %s"
            where_params.append(self.date_to)
        if self.invoice_ids:
            where_clause += " AND aml.invoice_id IN %s"
            where_params.append(tuple(self.invoice_ids.ids))
        if self.journal_ids:
            where_clause += " AND aml.journal_id IN %s"
            where_params.append(tuple(self.journal_ids.ids))
        if self.partner_ids:
            where_clause += " AND aml.partner_id IN %s"
            where_params.append(tuple(self.partner_ids.ids))
        sql_str = """
            SELECT
                aml.journal_id AS journal_id,
                array_agg(aml.id) AS move_line_ids
            FROM account_move_line aml
            LEFT JOIN account_move am
            ON aml.move_id = am.id {where} GROUP BY
            aml.journal_id""".format_map({'where': where_clause})
        self._cr.execute(sql_str, tuple(where_params))
        move_line_grouped_journal = self._cr.dictfetchall()

        # Get Account Move involved in the export
        sql_str = """
            SELECT array_agg(DISTINCT am.id) as account_moves
            FROM
                account_move_line aml
                INNER JOIN account_move am
                ON aml.move_id = am.id
            {where}
        """.format_map({'where': where_clause})
        self._cr.execute(sql_str, tuple(where_params))
        account_moves = self._cr.dictfetchall()[0]['account_moves']

        return move_line_grouped_journal, account_moves

    @api.model
    def get_journal_groupings(self, journal_id):
        '''
        @Function to get Journal Groupings
        '''
        grouping_fields = \
            self.env['account.journal'].browse(journal_id).group_fields
        return ["aml." + g_field.name for g_field in grouping_fields]
