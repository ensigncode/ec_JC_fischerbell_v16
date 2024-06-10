/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
console.log(publicWidget, "publicWidget")
var CustomForm = publicWidget.Widget.extend({
    selector: '#fitestraining_form',
    start: function() {
        $('.js-example-basic-multiple').select2();
    },

    events: {
        'change #reference_no': 'on_change_ref',
        'click .add_new_line': '_onClickAdd_new_line',
       	'click .remove_line': '_onClickRemove_line',
       	'click .custom_create': '_onClickSubmit',
    },

    on_change_ref: function(ev) {
        var reference_no = $(event.target).val();
        var clearFields = function() {
            ['#namee', '#partner_id', '#date_of_training', '#charge_name', '#phone', '#company_id', '#training_type', '#location'].forEach(function(field) {
                document.querySelector(field).value = '';
            });
        };
        if (reference_no) {
            this._rpc({
                model: 'fit.test.training',
                method: 'search_read',
                args: [[['reference_no','like',reference_no]],['name','name_of_trainer','date','charge_name','phone','company','training_types','location']],
                limit: 1,
            }).then(function(data) {
                if (data.length > 0) {
                    var namee = document.querySelector('#namee');
                    var partner_id = document.querySelector('#partner_id');
                    var date_of_training = document.querySelector('#date_of_training');
                    var charge_name = document.querySelector('#charge_name');
                    var phone = document.querySelector('#phone');
                    var company = document.querySelector('#company_id');
                    var training_types = document.querySelector('#training_type');
                    var location = document.querySelector('#location');
                    if (data[0]){
                        namee.value = data[0].name || '';
                        partner_id.value = data[0].name_of_trainer[0] || '';
                        date_of_training.value = data[0].date || '';
                        charge_name.value = data[0].charge_name || '';
                        phone.value = data[0].phone || '';
                        company.value = data[0].company[0] || '';
                        training_types.value = data[0].training_types || '';
                        location.value = data[0].location || '';
                    }
                } else {
                    clearFields();
                }
            });
        } else {
            clearFields();
        }
    },

    _onClickSubmit: async function(ev){
        	var self = this;
        	var fit_test_data = [];
        	var rows = $('.total_tranee > tbody > tr.info_line');
        	_.each(rows, function(row) {
            	let tranee_name = $(row).find('input[name="tranee_name"]').val();
            	let passport_no = $(row).find('input[name="passport_no"]').val();
            	let size = $(row).find('input[name="size"]').val();
            	console.log(tranee_name, passport_no, size)
            	fit_test_data.push({
                	'trainee': tranee_name,
                	'passport_no': passport_no,
                	'size':size,
            	});
        	});
        	$('textarea[name="fit_ids"]').val(JSON.stringify(fit_test_data));
   	},

   _onClickRemove_line: function(ev){
            var row = event.target.closest("tr");
            row.parentNode.removeChild(row);
    },

    _onClickAdd_new_line: function(ev){
                var $new_row = $('.add_extra_line').clone(true);
                $new_row.removeClass('d-none');
                $new_row.removeClass('add_extra_line');
                $new_row.addClass('info_line');
                $new_row.insertBefore($('.add_extra_line'));
                _.each($new_row.find('td'), function(val) {
                    $(val).find('input').attr('required', 'required');
                });
            },


});
publicWidget.registry.Many2many_tag = CustomForm;
return CustomForm;