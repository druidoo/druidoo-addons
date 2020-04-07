/* Copyright 2019 Druidoo - Iván Todorovich
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
odoo.define('pos_stock_lot_required.screens', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var core = require('web.core');
var _t = core._t;

screens.ActionpadWidget.include({
    renderElement: function() {
        var self = this;
        this._super();
        this.$('.pay').off('click').click(function(){
            var order = self.pos.get_order();
            var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                return line.has_valid_product_lot();
            });
            if(!has_valid_product_lot){
                self.gui.show_popup('alert', {
                    title: _t('Empty Serial/Lot Number'),
                    body: _t('One or more product(s) required serial/lot number.'),
                });
            }else{
                self.gui.show_screen('payment');
            }
        });
    }
});

});
