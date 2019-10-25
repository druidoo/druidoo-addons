from odoo import models, fields, api, _
from odoo.exceptions import UserError
import os
import base64
import tempfile
import paramiko
import logging
_logger = logging.getLogger(__name__)


class ConnectorSftpFetchfile(models.Model):
    _name = 'connector.sftp.fetchfile'
    _inherit = ['connector.sftp']
    _description = 'SFTP Configuration'

    name = fields.Char('Description')
    active = fields.Boolean(default=True)
    local_path = fields.Char('Local Directory',
                             default=tempfile.gettempdir()+'/',
                             required=True)
    remote_path = fields.Char('Remote Directory', required=True)
    remote_action = fields.Selection([('nothing', 'Do Nothing'),
                                      ('delete', 'Delete'),
                                      ('move', 'Move to another Path')],
                                     default='nothing', required=True)
    remote_move_path = fields.Char()
    file_ext = fields.Selection([('.cfo', 'CFONB'), ('.sh', 'SH')],
                                string='Files to Read', required=True)
    object_id = fields.Many2one('ir.model', 'Create a New Record',
                                required=True)
    local_file_remove = fields.Boolean('Remove Local Files')

    @api.model
    def check_path_vals(self, vals):
        remote_path = vals.get('remote_path')
        if remote_path:
            if not remote_path.endswith('/'):
                vals['remote_path'] = remote_path + '/'
        local_path = vals.get('local_path')
        if local_path:
            if not local_path.endswith('/'):
                vals['local_path'] = local_path + '/'
        return vals

    @api.model
    def create(self, vals):
        vals = self.check_path_vals(vals)
        return super(ConnectorSftpFetchfile, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self.check_path_vals(vals)
        return super(ConnectorSftpFetchfile, self).write(vals)

    @api.multi
    def test_connection(self):
        self.ensure_one()
        self._create_client()
        if self.client:
            self.client.close()
            raise UserError(_("Connection Test Succeeded! "
                              "Everything seems properly set up!"))
        return True

    @api.multi
    def fetch_files_to_demo_server(self):
        self.ensure_one()
        client = paramiko.client.SSHClient()
        client.load_system_host_keys()
        client.connect(
            hostname=self.host,
            username=self.username,
            password=self.password,
        )
        stdin, stdout, stderr = client.exec_command(
            'python /home/goldenom/CFONB/fetch_cfonb_file.py')
        client.close()
        _logger.info('files fetched to demo server...')

    @api.model
    def _cron_fetch_files_to_demo_server(self):
        configs = self.search([])
        for config in configs:
            config.fetch_files_to_demo_server()
        return True

    @api.multi
    def fetch_files(self):
        self.ensure_one()
        fetchfile = self.env['connector.sftp.fetchfile.file']
        self._create_client()
        files = self.client.listdir(self.remote_path)
        imported_files = fetchfile.search([]).mapped('name')
        processed_files = []
        for file in files:
            if file.endswith(self.file_ext) and file not in imported_files:
                self.client.get(self.remote_path+file, self.local_path+file)
                if self.object_id:
                    self.create_file_record(file)
                    processed_files.append(file)
        _logger.info('Fetched in local server:: %s' % str(processed_files))
        if self.remote_action == 'delete':
            self.remove_remote_files(processed_files)
        elif self.remote_action == 'move':
            self.move_remote_files(processed_files)
        if self.local_file_remove:
            self.remove_local_files(processed_files)
        self.client.close()
        return True

    @api.model
    def _cron_fetch_files(self):
        configs = self.search([])
        for config in configs:
            config.fetch_files()
        return True

    @api.multi
    def create_file_record(self, file):
        self.ensure_one()
        local_file = self.local_path + file
        if os.path.exists(local_file):
            with open(local_file, 'rb') as fp:
                contents = fp.read()
                rec = self.env[self.object_id.model].sudo().create({
                    'name': file,
                    'datas': base64.b64encode(contents),
                    'datas_fname': file,
                    'config_id': self.id,
                    'date_fetch': fields.Datetime.now(),
                    'import_state': 'to_import',
                })
                # rec.import_file()
            return rec.id

    @api.multi
    def remove_remote_files(self, files):
        self.ensure_one()
        for file in files:
            self.client.remove(self.remote_path+file)
        return True

    @api.multi
    def remove_local_files(self, files):
        self.ensure_one()

    @api.multi
    def move_remote_files(self, files):
        self.ensure_one()
        for file in files:
            self.client.posix_rename(self.remote_path+file,
                                     self.remote_move_path+file)
        return True


class ConnectorSftpFetchfileFile(models.Model):
    _name = 'connector.sftp.fetchfile.file'
    _inherit = ['connector.sftp.file', 'mail.thread']
    _description = 'Connector Fetchfile File'
    _order = 'date_fetch'

    name = fields.Char('File name', track_visibility='onchange')
    config_id = fields.Many2one('connector.sftp.fetchfile', 'Server Config.')
    import_state = fields.Selection(track_visibility='onchange')
    fail_reason = fields.Text(readonly=True)

    @api.multi
    def btn_retry(self):
        self.write({'import_state': 'to_import'})

    @api.multi
    def import_file(self):
        wiz_import = self.env['account.bank.statement.import']
        for rec in self:
            if str(rec.datas_fname).endswith('.cfo'):
                try:
                    wiz_bank_statements = wiz_import.create(
                        {'data_file': rec.datas, 'filename': rec.datas_fname})
                    wiz_bank_statements.import_file()
                    rec.import_state = 'imported'
                except Exception as e:
                    rec.write({'import_state': 'fail',
                               'fail_reason': str(e)})
                    _logger.error('Failed to import file:%s, '
                                  '%s' % (rec.datas_fname, e))
                    # break
        return True

    @api.model
    def _cron_import_files(self):
        recs = self.search([('import_state', '=', 'to_import')])
        recs.import_file()
