import functools
import itertools
import psycopg2

from odoo import fields, api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import mute_logger

import logging
_logger = logging.getLogger(__name__)


class UomUomMerge(models.TransientModel):
    _name = "uom.uom.merge"
    _description = "UoM Merge Wizard"

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        if active_model == 'uom.uom' and active_ids:
            res['uom_ids'] = active_ids
            res['target_uom_id'] = min(active_ids)
        return res

    uom_ids = fields.Many2many(
        "uom.uom",
        string="UoMs to merge",
        required=True,
    )

    target_uom_id = fields.Many2one(
        "uom.uom",
        string="Target UoM",
        help="The operations will be merged with this UoM",
        required=True,
    )

    @api.onchange('uom_ids')
    def _onchange_uom_ids(self):
        if (
            self.uom_ids
            and (
                not self.target_uom_id
                or self.target_uom_id not in self.uom_ids
            )
        ):
            self.target_uom_id = self.uom_ids[0]

    @api.model
    def get_fk_on(self, table):
        self._cr.execute("""
            SELECT
                cl1.relname as table,
                att1.attname as column
            FROM
                pg_constraint as con,
                pg_class as cl1,
                pg_class as cl2,
                pg_attribute as att1,
                pg_attribute as att2
            WHERE
                con.conrelid = cl1.oid
            AND con.confrelid = cl2.oid
            AND array_lower(con.conkey, 1) = 1
            AND con.conkey[1] = att1.attnum
            AND att1.attrelid = cl1.oid
            AND cl2.relname = %s
            AND att2.attname = 'id'
            AND array_lower(con.confkey, 1) = 1
            AND con.confkey[1] = att2.attnum
            AND att2.attrelid = cl2.oid
            AND con.contype = 'f'
        """, (table,))
        return self._cr.fetchall()

    @api.model
    def _update_foreign_keys(self, records, target):
        target.ensure_one()
        if records._name != target._name:
            raise ValidationError(_(
                "Records and target have to be of the same model\n"
                "%s != %s") % (records._name, target._name))
        _logger.debug(
            '_update_foreign_keys for target(%s): %s for records(%s): %r',
            target._name,
            target.id,
            records._name,
            records.ids,
        )

        # find the many2one relations
        for table, column in self.get_fk_on(records._table):
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name LIKE '%s'
            """ % (table)
            self._cr.execute(query, ())
            columns = []
            for data in self._cr.fetchall():
                if data[0] != column:
                    columns.append(data[0])

            query_dic = {
                'table': table,
                'column': column,
                'value': columns[0],
            }

            if len(columns) <= 1:
                # unique key treated
                query = """
                    UPDATE "%(table)s" as ___tu
                    SET %(column)s = %%s
                    WHERE
                        %(column)s = %%s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                %(column)s = %%s AND
                                ___tu.%(value)s = ___tw.%(value)s
                        )""" % query_dic
                for rec in records:
                    self._cr.execute(query, (target.id, rec.id, target.id))
            else:
                try:
                    with mute_logger('openerp.sql_db'), self._cr.savepoint():
                        query = """
                            UPDATE "%(table)s"
                            SET %(column)s = %%s
                            WHERE %(column)s IN %%s
                        """ % query_dic
                        self._cr.execute(query, (
                            target.id, tuple(records.ids)))

                        # Handle parents
                        if (
                            column == records._parent_name
                            and table == records._table
                        ):
                            query = """
                                WITH RECURSIVE cycle(id, %(column)s) AS (
                                        SELECT id, %(column)s
                                        FROM %(table)s
                                    UNION
                                        SELECT  cycle.id, t.%(column)s
                                        FROM    %(table)s AS t, cycle
                                        WHERE   t.id = cycle.%(column)s AND
                                                cycle.id != cycle.%(column)s
                                )
                                SELECT id FROM cycle
                                WHERE id = %(column)s AND id = %%s
                            """ % query_dic
                            self._cr.execute(query, (target.id,))
                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique
                    # constraint keeping record with nonexistent record is
                    # useless, better delete it
                    query = """
                        DELETE FROM "%(table)s"
                        WHERE "%(column)s" IN %%s
                    """ % query_dic
                    self._cr.execute(query, (tuple(records.ids),))

    @api.model
    def _update_reference_fields(self, records, target):
        target.ensure_one()
        if records._name != target._name:
            raise ValidationError(_(
                "Records and target have to be of the same model\n"
                "%s != %s") % (records._name, target._name))
        _logger.debug(
            '_update_reference_fields for target(%s): %s for records(%s): %r',
            target._name,
            target.id,
            records._name,
            records.ids,
        )

        def update_records(model, src, field_model='model', field_id='res_id'):
            if model not in self.env:
                return
            recs = self.env[model].sudo().search([
                (field_model, '=', records._name),
                (field_id, '=', src.id)])
            try:
                with mute_logger('openerp.sql_db'), self._cr.savepoint():
                    return recs.write({field_id: target.id})
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique
                # constraint keeping record with nonexistent record is useless,
                # better delete it
                return recs.unlink()

        update_records = functools.partial(update_records)

        for rec in records:
            update_records('calendar', src=rec, field_model='model_id.model')
            update_records('ir.attachment', src=rec, field_model='res_model')
            update_records('mail.followers', src=rec, field_model='res_model')
            update_records('mail.activity', src=rec, field_model='res_model')
            update_records('mail.message', src=rec)
            update_records('ir.model.data', src=rec)

        # remove duplicated __export__ ir.model.data
        self.env['ir.model.data'].search([
            ('model', '=', target._name),
            ('res_id', '=', target.id),
            ('module', '=', '__export__'),
        ]).unlink()

        records = self.env['ir.model.fields'].sudo().search([
            ('ttype', '=', 'reference')])
        for record in records:
            try:
                Model = self.env[record.model].sudo()
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue
            if field.compute is not None:
                continue
            for rec in records:
                Model.search([
                    (record.name, '=', '%s,%d' % (rec._name, rec.id))
                ]).write({
                    record.name: '%s,%d' % (target._name, target.id),
                })

    @api.model
    def _update_values(self, records, target):
        target.ensure_one()
        if records._name != target._name:
            raise ValidationError(_(
                "Records and target have to be of the same model\n"
                "%s != %s") % (records._name, target._name))
        _logger.debug(
            '_update_values for target(%s): %s for records(%s): %r',
            target._name,
            target.id,
            records._name,
            records.ids,
        )

        columns = target.fields_get().keys()

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item
        # get all fields that are not computed or x2many
        values = dict()
        for column in columns:
            field = target._fields[column]
            if (
                field.type not in ('many2many', 'one2many')
                and field.compute is None
            ):
                for item in itertools.chain(records, [target]):
                    if item[column]:
                        values[column] = write_serializer(item[column])
        # remove fields that can not be updated (id and parent_id)
        values.pop('id', None)
        parent_id = values.pop(target._parent_name, None)
        target.write(values)
        # try to update the parent_id
        if parent_id and parent_id != target.id:
            try:
                target.write({target._parent_name: parent_id})
            except ValidationError:
                _logger.info(
                    'Skip recursive record hierarchies for parent_id %s '
                    'of record: %s',
                    parent_id,
                    target.id,
                )

    @api.multi
    def merge(self):
        self.ensure_one()
        target = self.target_uom_id
        records = self.uom_ids
        # Sanity checks
        target.ensure_one()
        if records._name != target._name:
            raise ValidationError(_(
                "Records and target have to be of the same model\n"
                "%s != %s") % (records._name, target._name))
        if len(records) < 2:
            return
        if len(records.mapped('category_id')) > 1:
            raise UserError(_(
                "All uoms must belong to the same uom category."))
        # Check consistancy between uom values
        for rec in records:
            if target.uom_type == 'reference':
                if (
                    (rec.uom_type == 'bigger' and rec.factor_inv != 1.00)
                    or (rec.uom_type == 'smaller' and rec.factor != 1.00)
                ):
                    raise UserError(_(
                        "All uoms should represent the same quantities.\n"
                        "You can't merge uom with different conversion "
                        "factors."))
            else:
                if (
                    rec.uom_type != target.uom_type
                    or (
                        rec.uom_type == 'bigger'
                        and rec.factor_inv != target.factor_inv
                    ) or (
                        rec.uom_type == 'smaller'
                        and rec.factor != target.factor
                    )
                ):
                    raise UserError(_(
                        "All uoms should represent the same quantities.\n"
                        "You can't merge uom with different conversion "
                        "factors."))
        # Merge all
        records = records - target
        self._update_foreign_keys(records, target)
        self._update_reference_fields(records, target)
        self._update_values(records, target)
        _logger.info(
            '(uid = %s) merged the records(%s) %r with %s',
            self.env.user.id,
            records._name,
            records.ids,
            target.id,
        )
        # Notify
        if hasattr(target, 'message_post'):
            target.message_post(
                body='%s %s' % (
                    _("Merged with the following records:"),
                    ", ".join(
                        "%s (ID %s)" % (n[1], n[0])
                        for n in records.name_get()
                    )
                )
            )
        # Safely remove duplicates
        for rec in records:
            rec.unlink()
