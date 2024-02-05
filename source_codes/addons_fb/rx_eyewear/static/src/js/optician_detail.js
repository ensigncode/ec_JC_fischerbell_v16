odoo.define('rx_eyewear.optician_detail', function (require) {
    'use strict';

    var rpc = require('web.rpc');

        $(document).ready(function () {
            $(".s_optician_detail_form #name").on('change', function() {
                var inp_name = $(this).val();
                var inp_mobile  = $("#mobile").val();
                $('#company_id option').remove();
                rpc.query({
                    model: 'res.partner',
                    method: 'search_read',
                    args: [['|', ['name', 'ilike', inp_name],['mobile','=',inp_mobile]], ['id','name', 'mobile', 'parent_id']],
                }).then(function (data){
                    for (var i = 0; i < data.length; i++) {
                        var optionValue = data[i]['parent_id'][0]
                        var optionText = data[i]['parent_id'][1]
                        if (optionText) {
                            $('#company_id').append($('<option>').val(optionValue).text(optionText))
                        }
                    }
                    if(data.length == 0) {
                        rpc.query({
                            model: 'res.partner',
                            method: 'search_read',
                            args: [[['is_company', '=', true]], ['id','name']],
                        }).then(function (data1){
                            for (var i = 0; i < data1.length; i++) {
                                var optionValue = data1[i]['id']
                                var optionText = data1[i]['name']
                                if (optionText) {
                                    $('#company_id').append($('<option>').val(optionValue).text(optionText))
                                }
                            }
                        });
                    }
                });
            })
            
            
        });
    });
    