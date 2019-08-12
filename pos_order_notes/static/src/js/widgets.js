/* Copyright 2019 Druidoo - Iván Todorovich
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */
   
odoo.define('pos_order_notes.widgets', function (require) {
"use strict";

var core = require('web.core');
var screens = require('point_of_sale.screens');
var _t = core._t;

screens.OrderWidget.include({

    order_note_change: function() {
        console.log('Note changed!');
        this.renderElement('and_scroll_to_bottom');
    },

    bind_order_events: function() {
        this._super();
        var order = this.pos.get_order();
        order.unbind('change:note', this.order_note_change, this);
        order.bind('change:note', this.order_note_change, this);
    },

    renderElement: function(scrollbottom) {
        this._super.apply(this, arguments);
        var self = this;
        var el_note = this.el.querySelector('div.orderNote p');
        if (el_note) {
            el_note.addEventListener('click', function() {
                self.pos.get_order().display_notes_popup();
            });
        }
    },
});

});
