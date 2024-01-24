odoo.define('rx_eyewear.optician_detail', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

        $(document).ready(function () {
            $('.sale_order_create_btn').on('click', function () {
                var dataId = $(this).data('id');
                console.log('Data ID:', dataId);
                rpc.query({
                    model: 'optician.detail',
                    method: 'create_sale_order',
                    args: [[dataId]],
                }).then(function (data){
                    location.reload()
                });
                
            });
            
            
        });
    });
    