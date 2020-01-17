/* Copyright 2019 Druidoo - Iván Todorovich
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
   
odoo.define('pos_order_mgmt_draft_downpayment.models', function (require) {
'use strict';

var models = require('point_of_sale.models');

var OrderSuper = models.Order.prototype;
models.Order = models.Order.extend({
    init_from_JSON: function (json) {
        OrderSuper.init_from_JSON.apply(this, arguments);
        this.downpayment_order_id = json.downpayment_order_id;
    },
    export_as_JSON: function () {
        var res = OrderSuper.export_as_JSON.apply(this, arguments);
        res.downpayment_order_id = this.downpayment_order_id;
        return res;
    },
});

});
