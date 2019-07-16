from odoo import models, fields

import logging
_logger = logging.getLogger(__name__)


class AccountExportReportXLS(models.AbstractModel):
    _name = 'report.account_export.report_xls'
    _inherit = 'report.report_xlsx.abstract'

    def _get_template(self, export):
        template = {}
        columns = export.config_id._get_columns_dict()
        for field in export.config_id.field_ids:
            col = columns.get(field.field_type)
            template[field.id] = {
                'header': {
                    'type': 'string',
                    'value': field.name,
                },
                'line': {
                    'type': col.get('type', 'string'),
                    'value': self._render('line.get(%s, "")' % field.id),
                    'format': col.get('format', (
                        self.format_tcell_date_center
                        if col.get('type') == 'datetime'
                        else self.format_tcell_right
                        if col.get('type') == 'number'
                        else None
                    )),
                },
                'width': col.get('width', 18),
            }

            if field.field_type == 'amount'and \
                    export.config_id.credit_debit_format in ('01', 'DC'):
                template['%g_sense' % field.id] = {
                    'header': {'type': 'string', 'value': ''},
                    'line': {
                        'value': self._render(
                            'line.get("%g_sense")' % field.id)
                    },
                    'width': 5,
                }
        return template

    def _get_ws_params(self, wb, data, export):
        template = self._get_template(export)

        # Generate wanted list
        wl = []
        for field in export.config_id.field_ids:
            if field.field_type == 'amount'and \
                    export.config_id.credit_debit_format in ('01', 'DC'):
                wl.append('%g_sense' % field.id)
            wl.append(field.id)

        title = self._get_title(export)
        title_short = self._get_title(export)
        sheet_name = title_short[:31].replace('/', '-')
        params = {
            'ws_name': sheet_name,
            'generate_ws_method': '_account_export_report',
            'title': title,
            'wanted_list': wl,
            'col_specs': template,
        }
        return [params]

    def _get_title(self, export):
        title = '%s-%s' % (export.name, fields.Datetime.now())
        return title

    def _account_export_report(self, workbook, ws, ws_params, data, export):
        ws.set_landscape()
        ws.fit_to_pages(1, 0)
        ws.set_header(self.xls_headers['standard'])
        ws.set_footer(self.xls_footers['standard'])
        self._set_column_width(ws, ws_params)

        lines = export.get_account_move_line_data()

        row_pos = self._write_line(
            ws, 0, ws_params,
            col_specs_section='header',
            default_format=self.format_theader_yellow_left,
        )

        ws.freeze_panes(row_pos, 0)

        i=0
        for line in lines:
            i += 1
            _logger.warning('Writing line: %g/%g\n%s' % (i, len(lines), line))
            row_pos = self._write_line(
                ws, row_pos, ws_params,
                col_specs_section='line',
                render_space={'line': line},
                default_format=self.format_tcell_left,
            )
