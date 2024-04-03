odoo.define('portal_signature.claim_signature_form_file', function (require) {
'use strict';

var ajax = require('web.ajax');
var core = require('web.core');
var publicWidget = require('web.public.widget');
var NameAndSignature = require('web.name_and_signature').NameAndSignature;
var QWeb = core.qweb;
var rpc = require('web.rpc');

var _t = core._t;

$(document).ready(function(){
    let shadow;
    function dragit(event) {
        shadow = event.target;
    }
    function dragover(e) {
        let children = Array.from($(e.target).closest('tbody').children('tr'));
        if (children.indexOf($(e.target).closest('tr')[0]) > children.indexOf(shadow))
        $(e.target).closest('tr').after(shadow);
        else
        $(e.target).closest('tr').before(shadow);
    }
    $('tr[draggable="true"]').on('dragstart', dragit);
    $('tr[draggable="true"]').on('dragover', dragover);
    $(document).on('click', '.approve_btn', function (e) {
        e.preventDefault();
        var clickedButton = e.target;
        var dataIdValue = clickedButton.getAttribute('data-id');
        $('#modalsignatureaccept_'+dataIdValue).modal('show');
    });
    $(document).on('click', '.skip_delivery', function (e) {
        e.preventDefault();
        var clickedButton = e.target;
        var dataIdValue = clickedButton.getAttribute('data-id');
        $('#modaldeliveryskip_'+dataIdValue).modal('show');
    });
    $(document).on('click', '.submit_skip_delivery', function (e) {
        e.preventDefault();
        var clickedButton = e.target;
        var dataIdValue = clickedButton.getAttribute('data-id');
        var modalid = "#modaldeliveryskip_" + dataIdValue
        var reason_value = $(modalid).find('#skip_reason').val();
        rpc.query({
                    model: 'stock.picking',
                    method: 'send_notification_skip_delivery',
                    args: [[parseInt(dataIdValue)],reason_value],
                }).then(function (data){
                    if(data) {
                        window.location.reload()
                    }
                });
    });
});
});
