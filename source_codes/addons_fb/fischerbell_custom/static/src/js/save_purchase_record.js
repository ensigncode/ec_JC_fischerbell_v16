odoo.define('fischerbell_custom.save_purchase_record', function(require) {
    'use strict';
    var ajax = require('web.ajax');
    console.log("@@@@@@@@@@@@@@@@@@@@")

    $(document).ready(function() {
        'use strict';
         console.log("11111111111111111111")

        $('#js_lot').on('change', function(e) {
            console.log("22222222222222")
            var prod_value = $(this).val();
            console.log("###########prod_value",prod_value)
            var prod_id = $(this).attr('name');
            var old_products = JSON.parse(localStorage['product_list']);
            old_products[prod_id] = prod_value;
            localStorage.setItem('product_list', JSON.stringify(old_products));
            var old_price = JSON.parse(localStorage['product_price']);
            ajax.jsonRpc('/quickorder/price_calculate', 'call', {
                'price_count_id': prod_id,
                'prodcount': prod_value
            }).then(function(data) {
                $('input[id=' + prod_id + ']').val(data).change()
                old_price[prod_id] = data
                localStorage.setItem('product_price', JSON.stringify(old_price))
            })
        });
    });
}); 