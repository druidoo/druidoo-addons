odoo.define('website_snippet_blocklink.snippets.options', function (require) {
    'use strict';

    var core = require('web.core');
    var options = require('web_editor.snippets.options');
    var Dialog = require('web_editor.widget').Dialog;

    var _t = core._t;
    var qweb = core.qweb;

    options.registry.blocklink = options.Class.extend({
        xmlDependencies: ['/website_snippet_blocklink/static/src/xml/s_blocklink_modal.xml'],

        map: function(previewMode, value, $opt) {
            var self = this;
            this.dialog = new Dialog(this, {
                size: 'medium',
                title: _t("Customize link"),
                buttons: [
                    {
                        text: _t("Save"),
                        classes: 'btn-primary',
                        close: true,
                        click: function () {
                            if (!this.$('#href').val()) { this.$('#href').val('#'); }
                            self.$target.find('a').attr({'href': this.$('#href').val() });
                        }
                    },{
                        text: _t("Cancel"),
                        close: true
                    }
                ],
                $content: $(core.qweb.render('website_snippet_blocklink.s_blocklink_modal'))
            });
            this.dialog.opened().then((function () {
                this.$('#href').val(self.$target.find('a').attr('href'));
            }).bind(this.dialog));
            self.dialog.open();
        }

    });

});
