
odoo.define('pos_order_draft.models', function (require) {
    'use strict';

    var models = require('point_of_sale.models');

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        init_from_JSON: function (json) {
            _super_Order.init_from_JSON.apply(this, arguments);
            if (json.odoo_id) { this.odoo_id = json.odoo_id; }
            if (json.state) { this.state = json.state; }
        },
        export_as_JSON: function () {
            var res = _super_Order.export_as_JSON.apply(this, arguments);
            if (this.odoo_id) { res.odoo_id = this.odoo_id; }
            if (this.state) { res.state = this.state; }
            return res;
        },
    });

});
