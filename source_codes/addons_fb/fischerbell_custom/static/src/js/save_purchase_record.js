/** @odoo-module **/

import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
console.log("@@@@@@@@@@@@@@@@@@@@@00000")
export class PurchaseOrder extends FormController {
    /**
     * @override
     **/
    async saveRecord() {
            console.log("@@@@@@@@@@@@@@@@@@@@@111111")
            const res = await this._super(...arguments);
            console.log("@@@@@@@@@@@@@@@@@@@@@22222222")
            if (this.modelName === 'purchase.order') {
                this.displayNotification({ message: _t('Record Saved!'), type: 'success' });
            }
            return res;
        }
}

export const purchaseFormView = {
    ...formView,
    Controller: PurchaseOrder,
};

registry.category("views").add("purchase_form", purchaseFormView);
