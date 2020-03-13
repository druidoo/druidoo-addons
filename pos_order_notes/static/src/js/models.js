/* Copyright 2019 Druidoo - Iván Todorovich
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
   
odoo.define('pos_order_notes.models', function (require) {
'use strict';

var core = require('web.core');
var models = require('point_of_sale.models');
var _t = core._t

var OrderSuper = models.Order.prototype;
models.Order = models.Order.extend({

    init_from_JSON: function (json) {
        OrderSuper.init_from_JSON.apply(this, arguments);
        this.set('note', json.note);
    },

    export_as_JSON: function () {
        var res = OrderSuper.export_as_JSON.apply(this, arguments);
        res.note = this.get('note');
        return res;
    },

    export_for_printing: function () {
        var res = OrderSuper.export_for_printing.apply(this, arguments);
        res.note = this.get_note();
        return res;
    },

    set_note: function(value) {
        this.assert_editable();
        this.set('note', value);
    },

    get_note: function() {
        return this.get('note');
    },

    display_notes_popup: function() {
        var order = this;
        this.pos.gui.show_popup('textarea', {
            'title': _t('Notes and comments'),
            'value': order.get_note(),
            'confirm': function(val) {
                order.set_note(val);
            }
        });
    },

});

});
