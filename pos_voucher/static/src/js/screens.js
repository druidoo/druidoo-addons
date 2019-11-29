odoo.define('pos_voucher.screens', function (require) {
"use strict";

var PosBaseWidget = require('point_of_sale.BaseWidget');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var core = require('web.core');
var rpc = require('web.rpc');
var utils = require('web.utils');
var field_utils = require('web.field_utils');
var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents;
var screens = require('point_of_sale.screens');
var QWeb = core.qweb;
var _t = core._t;

var round_pr = utils.round_precision;

var voucherListScreenWidget = screens.ScreenWidget.extend({
    template: 'voucherListScreenWidget',

    init: function(parent, options){
        this._super(parent, options);
        this.voucher_cache = new screens.DomCache();
        this.new_voucher = null;
    },

    auto_back: true,

    show: function(){
        var self = this;
        this._super();
        this.new_voucher = null;
        this.renderElement();
        this.details_visible = false;
        this.old_voucher = this.pos.get_order().voucher_id;
        this.$('.back').click(function(){
            self.gui.back();
            this.new_voucher = null;
        });

        this.$('.next').click(function(){   
            var current_order = self.pos.get('selectedOrder');
            var voucher = self.new_voucher;
            if (!voucher)
            {
                return self.gui.show_popup('alert', {
                            title: _t('Warning'),
                            body: _t('Please select a Voucher'),
                        });
            }
            current_order.voucher_id = voucher.id;
            var voucher_register = null;
            if (voucher.type_id)
            {
                var voucher_type_search = self.pos.voucher_type_by_id[voucher.type_id[0]];
                if(voucher_type_search)
                {
                    voucher_register = _.find(self.pos.cashregisters, function (cashregister) {
                        return cashregister.journal['id'] == voucher_type_search['journal_id'][0];
                    });
                }
            }
            if (!voucher_register){
                return self.gui.show_popup('alert', {
                            title: _t('Configuration Warning'),
                            body: _t('Please configure '+ voucher_type_search['journal_id'][1] + ' as a payment method in your POS.'),
                        });
            }
            if (voucher['partner_id'] && voucher['partner_id'][0]) {
                var client = self.pos.db.get_partner_by_id(voucher['partner_id'][0]);
                if (client) {
                    current_order.set_client(client)
                }
            }
            var amount = voucher.pending_amount;
            
            var paymentlines = current_order.paymentlines;
            for (var i = 0; i < paymentlines.models.length; i++) {
                var payment_line = paymentlines.models[i];
                if (payment_line.cashregister.journal['id'] == voucher_register['journal'].id) {
                    payment_line.destroy();
                }
            }
            var voucher_paymentline = new models.Paymentline({}, {
                order: current_order,
                cashregister: voucher_register,
                pos: self.pos
            });
            var due = current_order.get_due();
            if (amount >= due) {
                voucher_paymentline.set_amount(due);
            } else {
                voucher_paymentline.set_amount(amount);
            }
            voucher_paymentline['voucher_id'] = voucher['id'];
            voucher_paymentline['voucher_code'] = voucher['code'];
            current_order.paymentlines.add(voucher_paymentline);
            current_order.trigger('change', current_order);
            self.gui.back();
        });
        var partner_id = this.pos.get('selectedOrder').get_client();

        if (partner_id)
        {
            var vouchers = this.pos.voucher_by_customer[partner_id.id];
            if (vouchers)
            {
            this.render_list(vouchers);
            }
        }
        this.$('.voucher-list-contents').delegate('.client-list','click',function(event){
            self.line_select(event,$(this),parseInt($(this).data('id')));
        });

        var search_timeout = null;

        if(this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard){
            this.chrome.widget.keyboard.connect(this.$('.searchbox input'));
        }

        this.$('.searchbox input').on('keypress',function(event){
            clearTimeout(search_timeout);

            var searchbox = this;

            search_timeout = setTimeout(function(){
                self.perform_search(searchbox.value, event.which === 13);
            },70);
        });

        this.$('.searchbox .search-clear').click(function(){
            self.clear_search();
        });
    },
    hide: function () {
        this._super();
        this.new_voucher = null;
    },
    
    render_list: function(vouchers){
        var contents = this.$el[0].querySelector('.voucher-list-contents');
        contents.innerHTML = "";
        for(var i = 0, len = Math.min(vouchers.length,1000); i < len; i++){
            var voucher    = vouchers[i];
            var voucherline = this.voucher_cache.get_node(voucher.id);
            if(!voucherline){
                var voucherline_html = QWeb.render('voucherLine',{widget: this, voucher:vouchers[i]});
                var voucherline = document.createElement('tbody');
                voucherline.innerHTML = voucherline_html;
                voucherline = voucherline.childNodes[1];
                this.voucher_cache.cache_node(voucher.id,voucherline);
            }
            if( voucher.id === this.old_voucher ){
                voucherline.classList.add('highlight');
            }else{
                voucherline.classList.remove('highlight');
            }
            contents.appendChild(voucherline);
        }
    },
    
    has_voucher_changed: function(){
        if( this.old_voucher && this.new_voucher ){
            return this.old_voucher.id !== this.new_voucher.id;
        }else{
            return !!this.old_voucher !== !!this.new_voucher;
        }
    },
    
    line_select: function(event,$line,id){
        var voucher = this.pos.voucher_by_id[id];
        this.$('.client-list .lowlight').removeClass('lowlight');
        if ( $line.hasClass('highlight') ){
            $line.removeClass('highlight');
            $line.addClass('lowlight');
            this.new_voucher = null;
        }else{
            this.$('.client-list .highlight').removeClass('highlight');
            $line.addClass('highlight');
            var y = event.pageY - $line.parent().offset().top;
            this.new_voucher = voucher;
        }
    },

    close: function(){
        this._super();
        if (this.pos.config.iface_vkeyboard && this.chrome.widget.keyboard) {
            this.chrome.widget.keyboard.hide();
        }
    },
});
gui.define_screen({name:'voucherlist', widget: voucherListScreenWidget});

return {
    voucherListScreenWidget: voucherListScreenWidget,
};

});
