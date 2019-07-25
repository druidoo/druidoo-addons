
odoo.define('pos_order_draft.models', function (require) {
    'use strict';

    var models = require('point_of_sale.models');
    var OrderSuper = models.Order.prototype;
    models.Order = models.Order.extend({
        init_from_JSON: function (json) {
            OrderSuper.init_from_JSON.apply(this, arguments);
            this.odoo_id = json.odoo_id;
            this.state = json.state;
        },
        export_as_JSON: function () {
            var res = OrderSuper.export_as_JSON.apply(this, arguments);
            res.odoo_id = this.odoo_id;
            res.state = this.state;
            return res;
        },
    });

});
