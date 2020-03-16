odoo.define('pos_voucher.pos_voucher', function (require) {
"use strict";

    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var _t = core._t;
    var QWeb = core.qweb;

    models.load_fields("account.bank.statement", ['is_voucher']);

    models.load_models({
        model: 'pos.voucher',
        fields: ['code', 'type_id', 'partner_id', 'start_date', 'end_date', 'pending_amount', 'total_amount'],
        domain: [['state', 'in', ['validated', 'partially_consumed']]],
        context: {'pos': true},
        loaded: function (self, vouchers) {
            self.vouchers = vouchers;
            self.voucher_by_id = {};
            self.voucher_by_customer = {};
            for (var x = 0; x < vouchers.length; x++) {
                self.voucher_by_id[vouchers[x].id] = vouchers[x];
                if (!self.voucher_by_customer[vouchers[x].partner_id[0]]) {
                    self.voucher_by_customer[vouchers[x].partner_id[0]] = [vouchers[x]];
                }
                else{
                    self.voucher_by_customer[vouchers[x].partner_id[0]].push(vouchers[x]);
                }
            }
        }
    });

    models.load_models({
        model: 'pos.voucher.type',
        fields: ['name', 'journal_id','product_id'],
        domain: [['available_in_pos','=',true]],
        context: {'pos': true},
        loaded: function (self, vouchers_type) {
            self.vouchers_type = vouchers_type;
            self.voucher_type_by_id = {};
            for (var x = 0; x < vouchers_type.length; x++) {
                self.voucher_type_by_id[vouchers_type[x].id] = vouchers_type[x];
            }
        }
    });

    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this, arguments);
            if (this.voucher_id) {
                json.voucher_id = parseInt(this.voucher_id);
            }
            return json;
        },
        is_voucher_order: function(){
            var is_voucher = 0;
            var self = this;
            var order = this.pos.get_order();
            if (!order) {
                return is_voucher;
            }
            var orderlines = order.get_orderlines();
            var is_voucher_line = 0;
            for(var i = 0, len = orderlines.length; i < len; i++){
                var orderline = orderlines[i];
                if (orderline && orderline.voucher_type_id){
                    is_voucher = 1;
                    break;
                }
            }
            return is_voucher;
        },
    });


    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function() {
            var res = _super_orderline.initialize.apply(this,arguments);
            this.voucher_type_id = false;
            this.pos_voucher_code = '';
            return res;
        },
        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.apply(this,arguments);
            if (this.voucher_type_id){
                json.voucher_type_id = this.voucher_type_id;
            }
            if (this.pos_voucher_code){
                json.pos_voucher_code = this.pos_voucher_code;
            }
            return json;
        },
        init_from_JSON: function(json){
            var res = _super_orderline.init_from_JSON.apply(this,arguments);
            if (json.voucher_type_id){
                this.voucher_type_id = json.voucher_type_id;
            }
            if (json.pos_voucher_code){
                this.pos_voucher_code = json.pos_voucher_code;
            }
            return res;
        },
        set_pos_voucher_code: function(pos_voucher_code){
            this.pos_voucher_code = pos_voucher_code;
            this.trigger('change',this);
        },
        get_pos_voucher_code: function(){
            return this.pos_voucher_code;
        },
    });

});
