# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import csv
import pytz
import shutil
import tempfile

from datetime import datetime, date


from odoo import api, fields, models
from odoo.tools import ustr


class AccountExport(models.Model):
    _name = "account.export"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        'Export filename', size=32, required=True,
        default=lambda self: self._get_default_name())
    extension = fields.Selection([('csv', 'Csv')], 'Extension', default='csv',
                                 required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('exported', 'Exported')], 'State',
        default='draft')
    last_export_date = fields.Datetime(
        string='Last Export Date', compute='_get_last_export_date',
        readonly=True, help='Last date of export')
    # Options
    filter_move_lines = fields.Selection([
        ('all', 'Export all move lines'),
        ('non_exported', 'Export only non exported move lines')],
        'Move lines to export', default='non_exported')
    # Filters
    date_from = fields.Date('From date')
    date_to = fields.Date('To date')
    invoice_ids = fields.Many2many('account.invoice', string='Invoice')
    journal_ids = fields.Many2many(
        'account.journal', string='Account Journals')
    partner_ids = fields.Many2many('res.partner', string='Partner')
    config_id = fields.Many2one(
        string='Export Configuration', comodel_name='account.export.config',
        default=lambda self: self._get_default_config(), required=True)

    # ############## MODEL FUNCTION FIELDS #####################

    @api.one
    def _get_last_export_date(self):
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
            [('is_default', '=', True)])
        if not config:
            config = self.env['account.export.config'].search([])
        return config and config[0].id or False

    # ################## EXPORTING FUNCTIONS ####################

    @api.multi
    def create_report(self):
        '''
        @Function to generate the report
        '''
        self.ensure_one()
        self.HEADER = self.build_header()

        # Prepare data to export to file
        datas = self.get_account_move_line_data()

        # Generate the file based
        moves_file = False
        if self.extension == 'csv':
            moves_file = self.get_data_csv_file(
                datas, str(self.config_id.csv_separator))

        if not moves_file:
            return True

        # Create a document with output as content
        user_tz = self.env.user.tz or 'Europe/Paris'
        now_at_utc = fields.Datetime.from_string(fields.Datetime.now())
        local = pytz.timezone(user_tz)
        now_at_local = pytz.utc.localize(now_at_utc).astimezone(local)
        now_at_local = fields.Datetime.to_string(now_at_local)

        attachment_name = "{}-{}.{}".format(
                self.name, now_at_local, self.extension)
        vals = {
            'name': attachment_name,
            'type': 'binary',
            'datas': moves_file,
            'datas_fname': attachment_name,
            'res_model': 'account.export',
            'res_id': self.id,
        }
        self.env["ir.attachment"].create(vals)

        # Change report state to exported
        self.state = 'exported'
        return True

    @api.model
    def get_data_csv_file(self, source_data, delimiter_separator=","):
        '''
        @Function to write the data into csv file and return the binary data
            @Params:
                source_data: List of data
                delimiter_separator: Delimeter separator, comma by default
        '''
        tmp_directory = tempfile.mkdtemp()
        file_path = tmp_directory + '/tmp_file.csv'
        csvfile = open(file_path, 'w')

        csv_writer = csv.writer(csvfile, delimiter=delimiter_separator)

        for line in source_data:
            # Encode the string to utf8 before writing
            new_line = [u"{}".format(item) for item in line]
            csv_writer.writerow(new_line)

        csvfile.close()
        csvfile = open(file_path, 'rb')
        data = base64.encodestring(csvfile.read())

        # Remove the temporary directory
        try:
            shutil.rmtree(tmp_directory)
        except:
            print('Can not remove directory: ', tmp_directory)
        return data

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
        output = self.HEADER and [self.HEADER] or []

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

        # Get footer
        footer = self.build_footer()
        if footer:
            output += [footer]
        return output

    @api.model
    def get_report_line_data(self, groupings, move_line_ids):
        '''
        @Function to get the final data line
        '''
        res = []
        if groupings:
            # Finding the move lines which can be grouped together
            grouping_str = ", ".join(groupings)
            sql_query = """
                SELECT %s, array_agg(aml.id) as move_line_ids
                FROM account_move_line aml
                WHERE aml.id IN %s
                GROUP BY %s
            """
            sql_query = sql_query % (grouping_str, str(tuple(move_line_ids)),
                                     grouping_str)

            self._cr.execute(sql_query)
            grouped_move_lines = self._cr.dictfetchall()

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
                        COALESCE (aml.ref, '') || COALESCE(rp.name, '')
                    END
                ) AS account_move_name,

                aml.debit,
                aml.credit
            FROM
                 account_move_line aml
                 LEFT JOIN account_journal aj ON aml.journal_id = aj.id
                 LEFT JOIN account_move am ON aml.move_id = am.id
                 LEFT JOIN res_partner rp ON aml.partner_id = rp.id
                 LEFT JOIN account_account aa ON aml.account_id = aa.id
            WHERE aml.id IN (%s)
        """
        sql_str = sql_str % ', '.join(map(str, move_line_ids))

        self._cr.execute(sql_str)
        move_line_data = self._cr.dictfetchall()

        # Get data of the first line
        first_line = move_line_data[0]
        export_code = first_line['export_code']
        move_line_date = first_line['date']
        move_number = first_line['move_number']
        export_account_code = first_line['export_account_code']
        journal_code = first_line['journal_code']

        account_move_name = first_line['account_move_name']
        debit = 0.0
        credit = 0.0

        # Group the data of account move lines if groupings are set.
        # Otherwise, the result is the data of the first line
        if groupings:
            for line in move_line_data:
                if export_code and export_code != "GROUPED" and \
                    export_code != 'NO-JOURNAL-CODE' and \
                        export_code != line['export_code']:
                    export_code = "GROUPED"

                if move_line_date and move_line_date != "GROUPED" and \
                        move_line_date != line["date"]:
                    move_line_date = "GROUPED"

                if move_number and move_number != "GROUPED" and \
                        move_number != line['move_number']:
                    move_number = "GROUPED"

                if export_account_code and \
                    export_account_code != "GROUPED" and \
                        export_account_code != line['account_code']:
                    export_account_code = "GROUPED"
                if account_move_name and account_move_name != "GROUPED" and \
                        account_move_name != line['account_move_name']:
                    account_move_name = "GROUPED"
                debit += line['debit']
                credit += line['credit']
        else:
            debit = first_line['debit']
            credit = first_line['credit']

        if not export_code and journal_code:
            export_code = journal_code

        # Refreshing the data before export
        export_code = export_code != 'NO-JOURNAL-CODE' and export_code or ""

        # Format credit/debit based on format
        credit_debit_format = \
            self.config_id and self.config_id.credit_debit_format or '01'
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

        # Format number / decimal point
        amount = ustr(amount)
        amount = amount[:14].replace('.', self.get_decimal_point())

        # Format dates to software format
        try:
            move_line_date = \
                self.convert_to_software_date_format(move_line_date)
        except:
            pass

        account_move_name = account_move_name and account_move_name[:13] or ''

        res_data = [
            export_code,
            move_line_date,
            move_number,
            export_account_code,
            account_move_name,
        ]

        if credit_debit_format in ('01', 'DC'):
            res_data.append(sense)

        res_data.append(amount)

        # Replace the column with False Value by the header column name
        final_data = []
        pos = 0
        for item in res_data:
            new_item = item and item or ''
            if new_item == "GROUPED":
                try:
                    new_item = self.HEADER[pos]
                except:
                    # Set value to empty string if the item position is greater
                    # than the header size
                    new_item = ""
            pos += 1
            final_data.append(u'{}'.format(new_item))
        return final_data

    @api.model
    def build_header(self):
        '''
        @Function Use the default header if it is set, otherwise, use thje
        '''
        header = self.config_id and self.config_id.header and \
            self.config_id.header.split(",") or []
        # Strip the leading and trailling spaces
        header = [item.strip() for item in header]
        return header

    @api.model
    def build_footer(self):
        return self.config_id and \
            self.config_id.footer and \
            self.config_id.footer.split(",") or []

    # ########### OTHER FUNCTIONS FOR GETTING DATA #############

    @api.multi
    def get_account_move_line_group_by_journal(self):
        '''
        @Function to get
            - account move line list grouped by journal
            - account move list involved
        '''
        # Building the Where Clause
        WHERE_CLAUSE = """
            WHERE am.state <> 'draft'
        """
        # Options
        if self.filter_move_lines == 'non_exported':
            WHERE_CLAUSE += "\n AND am.exported IS NOT TRUE"

        # Filters
        if self.date_from:
            WHERE_CLAUSE += "\n AND aml.date >= '%s'" % self.date_from
        if self.date_to:
            WHERE_CLAUSE += "\n AND aml.date <= '%s'" % self.date_to
        if self.invoice_ids:
            WHERE_CLAUSE += \
                "\n AND aml.invoice_id IN (%s)" % ', '.join(
                    map(str, self.invoice_ids.ids))
        if self.journal_ids:
            WHERE_CLAUSE += \
                "\n AND aml.journal_id IN (%s)" % ', '.join(
                    map(str, self.journal_ids.ids))
        if self.partner_ids:
            WHERE_CLAUSE += \
                "\n AND aml.partner_id IN (%s)" % ', '.join(
                    map(str, self.partner_ids.ids))

        SQL_STR = """
            SELECT
                aml.journal_id AS journal_id,
                array_agg(aml.id) AS move_line_ids
            FROM account_move_line aml
            LEFT JOIN account_move am
            ON aml.move_id = am.id
            %s
            GROUP BY aml.journal_id
        """ % WHERE_CLAUSE

        self._cr.execute(SQL_STR)
        move_line_grouped_journal = self._cr.dictfetchall()

        # Get Account Move involved in the export
        SQL_STR = """
            SELECT array_agg(DISTINCT am.id) as account_moves
            FROM
                account_move_line aml
                INNER JOIN account_move am
                ON aml.move_id = am.id
            %s
        """ % WHERE_CLAUSE

        self._cr.execute(SQL_STR)
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

    @api.model
    def get_decimal_point(self):
        '''
        @Function to get the decimal separator based on the user language
        '''
        user = self.env['res.users'].browse(self._uid)
        user_lang_code = user.lang or 'en_US'
        user_lang = self.env['res.lang'].search(
            [('code', '=', user_lang_code)],
            limit=1)
        return user_lang and user_lang.decimal_point or '.'

    def convert_to_software_date_format(self, date):
        dateformat = self.config_id and self.config_id.dateformat or "%d%m%y"
        return datetime.strptime(str(date), "%Y-%m-%d").strftime(dateformat)
