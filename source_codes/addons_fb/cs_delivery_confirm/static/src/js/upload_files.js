/** @odoo-module **/

import MainComponent from '@stock_barcode/components/main';
import { patch } from 'web.utils';
import { useService } from "@web/core/utils/hooks";

var ajax = require('web.ajax');

patch(MainComponent.prototype, 'cs_delivery_confirm', {
    setup() {
        this._super(...arguments);
        this.rpc = useService("rpc");
        this.notification = useService('notification');
    },

    async uploadFiles() {
        var self = this;
        const recordId = this.props.id;
        const recordModel = this.props.model
        const fileInput = document.getElementById("files");
        const files = fileInput.files;
        var formData = new FormData();
        formData.append('record_id', recordId);
        formData.append('record_model', recordModel);

        _.each(files, function (file) {
            formData.append('attachment_files', file, file.name);
        });
        
        if (files.length === 0) {
            this.notification.add("No files selected !!", {type: 'danger'});
            return ;
        }
        
        $.ajax({
            url: '/files_upload',
            type: 'POST',
            data: formData,
            cache: false,
            contentType: false,
            processData: false,
            success: function (data) {
                self.notification.add("Files successfully uploaded !!", {type: 'success'});
            },
            error: function (xhr, status, error) {
                self.notification.add("Failed to send files !!", {type: 'success'});
            },
        });
        $(fileInput).val('');

    },
});