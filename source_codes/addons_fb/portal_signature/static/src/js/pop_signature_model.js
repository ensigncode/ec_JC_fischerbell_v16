odoo.define('portal_signature.claim_signature_form_file', function (require) {
'use strict';

var ajax = require('web.ajax');
var core = require('web.core');
var publicWidget = require('web.public.widget');
var NameAndSignature = require('web.name_and_signature').NameAndSignature;
var QWeb = core.qweb;

var _t = core._t;

$(document).ready(function(){

    $(document).on('click', '.approve_btn', function (e) {
        e.preventDefault();
        var clickedButton = e.target;
        var dataIdValue = clickedButton.getAttribute('data-id');
        $('#modalsignatureaccept_'+dataIdValue).modal('show');
    });
    // $(document).on('click', '.o_portal_sign_submit', function (e) {
    //     e.preventDefault();
    //     $('#modalsignatureaccept').modal('hide');
    // });
});
});
