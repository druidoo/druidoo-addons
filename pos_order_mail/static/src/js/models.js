odoo.define('pos_order_mail.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');


    var PosModelSuper = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        push_and_invoice_order: function(order) {
            var client = order.get_client()
            if (order.is_to_send_mail() && client && !client.email) {
                var res = new $.Deferred();
                res.reject({code:400, message:'Missing Customer Email', data:{}});
                return res;
            }
            // super
            return PosModelSuper.push_and_invoice_order.apply(this, arguments);
        },
    })


    var OrderSuper = models.Order.prototype;
    models.Order = models.Order.extend({

        initialize: function(attributes, options) {
            OrderSuper.initialize.apply(this, arguments);
            this.to_send_mail = false;
        },

        set_to_send_mail: function(to_send_mail) {
            this.assert_editable();
            this.to_send_mail = to_send_mail;
        },

        is_to_send_mail: function() {
            return this.to_send_mail;
        },

        init_from_JSON: function (json) {
            OrderSuper.init_from_JSON.apply(this, arguments);
            this.to_send_mail = json.to_send_mail;
        },

        export_as_JSON: function () {
            var res = OrderSuper.export_as_JSON.apply(this, arguments);
            res.to_send_mail = this.to_send_mail;
            return res;
        },
    });

})
