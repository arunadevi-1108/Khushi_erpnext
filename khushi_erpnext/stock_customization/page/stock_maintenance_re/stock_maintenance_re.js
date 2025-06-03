let previous_comparison_type = null;
frappe.pages['stock-maintenance-re'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Stock Maintenance Report',
        single_column: true
    });

    let filter_fields = [
        {fieldname: "warehouse", label: "Warehouse", fieldtype: "Link", options: 'Warehouse'},
        {fieldname: "item_group", label: "Item Group", fieldtype: "Link", options: "Item Group"},
        {fieldname: "brand", label: "Brand", fieldtype: "Link", options: "Brand"},
        {fieldname: "year", label: "Year", fieldtype: "Link", options: 'Year'},
        {fieldname: "subject", label: "Subject", fieldtype: "Link", options: 'Subject'},
        {fieldname: "status", label: "Status", fieldtype: "Select", options: ["","Continue", "SemiContinue", "Discontinue"]},
        {fieldname: "season", label: "Season", fieldtype: "Link", options: 'Item Segment'},
        {fieldname: "item", label: "Item", fieldtype: "Link", options: "Item"},
        {fieldname: "comparison_type", label: "Comparison Type", fieldtype: "Link", options: "Comparison Type"},
        {fieldname: "qty", label: "Qty", fieldtype: "Int"},
        {fieldname: "qty_from", label: "Qty From", fieldtype: "Int"},
        {fieldname: "qty_to", label: "Qty To", fieldtype: "Int"},
        { fieldname: "page_size", label: "Page Size", fieldtype: "Select", options: [150, 250, 500, 2500, "All"] , default:150 }
    ];

    // Initialize Filters
        filter_fields.forEach(function(field) {
            let previous_value = null;
            page.add_field({
                fieldname: field.fieldname,
                label: field.label,
                fieldtype: field.fieldtype,
                default: field.default || '',
                options: field.options || '',
                change: function() {
                    const current_value = page.fields_dict[field.fieldname].get_value();
                    if (current_value !== previous_value) {
                        previous_value = current_value;
                        update_dashboard();
                    }
                }
            });
        });

    // Create the grid container
    let grid_container = $('<div></div>').css({
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',  // Dynamically adjust to fit the screen size
        gap: '20px',
        marginTop: '20px',
    }).appendTo(page.body);

    //  Based the filter hide or display's the page fields
    function toggle_display_by_filters(filters){
        if (filters.comparison_type === 'Between') {
            page.fields_dict.qty.$wrapper.css("display", "none");
            page.fields_dict.qty_from.$wrapper.css("display", "block");
            page.fields_dict.qty_to.$wrapper.css("display", "block");
        } else if (filters.comparison_type) {
            page.fields_dict.qty.$wrapper.css("display", "block");
            page.fields_dict.qty_from.$wrapper.css("display", "none");
            page.fields_dict.qty_to.$wrapper.css("display", "none");
        } else {
            page.fields_dict.qty.$wrapper.css("display", "none");
            page.fields_dict.qty_from.$wrapper.css("display", "none");
            page.fields_dict.qty_to.$wrapper.css("display", "none");
        }

    }

    //  Reset the quantity fields based on the comparison_type
    function reset_quantity_fields_and_return_updated_filters(){
        let filters = get_filters_value()
        const current_comparison_type = page.fields_dict.comparison_type.get_value()
        if ( current_comparison_type != previous_comparison_type ){
            page.fields_dict.qty.set_value(null);
            page.fields_dict.qty_from.set_value(null);
            page.fields_dict.qty_to.set_value(null);
            filters.qty =  null
            filters.qty_from =  null
            filters.qty_to = null
            previous_comparison_type = filters.comparison_type;
        }
        return filters
    }

    //  Retrieve data from the backend and process it for display
    function get_data_and_display(filters){
            frappe.call({
                method: "khushi_erpnext.stock_customization.page.stock_maintenance_re.stock_maintenance_re.get_data",
                args: {
                    filters: filters,
                },
                freeze: true,
                freeze_message: "Loading",
                callback: function (r) {
                    grid_container.empty();
                    display_report_data(r.message[0],r.message[1],r.message[2]);
                }
            });
    }

    //  Retrieves the Filter Value
    function get_filters_value(){
        let filters = {
            warehouse: page.fields_dict.warehouse.get_value(),
            item_group: page.fields_dict.item_group.get_value(),
            brand: page.fields_dict.brand.get_value(),
            year: page.fields_dict.year.get_value(),
            subject: page.fields_dict.subject.get_value(),
            status: page.fields_dict.status.get_value(),
            season: page.fields_dict.season.get_value(),
            item: page.fields_dict.item.get_value(),
            comparison_type: page.fields_dict.comparison_type.get_value(),
            qty: page.fields_dict.qty ? page.fields_dict.qty.get_value() : null,
            qty_from: page.fields_dict.qty_from ? page.fields_dict.qty_from.get_value() : null,
            qty_to: page.fields_dict.qty_to ? page.fields_dict.qty_to.get_value() : null,
            page_limit: page.fields_dict.page_size.get_value()
        };
        return filters

    }

    //  To Update Dashboard
    function update_dashboard() {
        let filters = reset_quantity_fields_and_return_updated_filters()
        toggle_display_by_filters(filters)
        if (filters.comparison_type) {
            if(filters.qty !== null ||  ((filters.qty_from !==null && filters.qty_to !== null))){
                page.wrapper.find('.loading-spinner').show();
                get_data_and_display(filters)
            }
        }
        else {
            get_data_and_display(filters)
        }
    }


    // To reset the filters
    function reset_filters() {
        filter_fields.forEach(function (field) {
            if (field.fieldname === "page_size") {
                page.fields_dict[field.fieldname].set_value(150);
            } else {
                page.fields_dict[field.fieldname].set_value('');
            }
        });
        update_dashboard();
    }
    // Add the Reset Filters button
    page.add_button('Reset Filters', reset_filters);

    page.add_button('Send WhatsApp Notification', function() {
        let selected_items = [];

        grid_container.find('.item-checkbox:checked').each(function() {
            let item_div = $(this).closest('.item-container');
            let item_code_text = item_div.find('div').first().text();
            let item_code = item_code_text.replace('Item: ', '').trim();
            selected_items.push(item_code);
        });

        if (selected_items.length === 0) {
            frappe.msgprint('No items selected!');
            return;
        }

        frappe.call({
        method: 'frappe_whatsapp.utils.get_phone_number',
        callback: function (r) {
            if (r.message) {
                let phone_number_list = r.message

            let d = new frappe.ui.Dialog({
                title: 'Send WhatsApp Notification',
                fields: [
                    {
                        label: 'WhatsApp Template',
                        fieldname: 'whatsapp_template',
                        fieldtype: 'Link',
                        options: 'WhatsApp Notification',
                        reqd: 1
                    },
                    {
                        fieldtype: 'Section Break'
                    },
                    {
                        fieldname: 'multi_doc_to_pdf',
                        label: 'Multiple Doc to PDF ',
                        fieldtype: 'Check',
                        default: 1
                    },
                    {
                        fieldtype: 'Section Break',
                        label: 'Send To Options'
                    },
                    {
                        fieldname: 'send_group',
                        label: 'Send to Group',
                        fieldtype: 'Check',
                        default: 0
                    },
                    {
                        fieldname: 'send_individual',
                        label: 'Send to Individual',
                        fieldtype: 'Check',
                        default: 0,
                    },
                    {
                        fieldtype: 'Column Break'
                    },
                    {
                        fieldname: 'group',
                        label: 'Group',
                        fieldtype: 'Link',
                        options: 'WhatsApp Group',
                        depends_on: 'eval:doc.send_group==1'

                    },
                    {
                        fieldtype: 'Column Break'
                    },
                    {
                        fieldname: 'individual',
                        label: 'Individual',
                        fieldtype: 'Autocomplete',
                        options: phone_number_list,
                        depends_on: 'eval:doc.send_individual==1'
                    },
                    {
                        fieldtype: 'Section Break'
                    }
                ],
                primary_action_label: 'Send',
                primary_action(values) {
                    if (!values.whatsapp_template) {
                        frappe.msgprint('WhatsApp Template is required!');
                        return;
                    }

                    frappe.call({
                        method: "frappe_whatsapp.utils.trigger_bulk_wp_notification",
                        args: {
                            reference_names: selected_items,
                            template_name: values.whatsapp_template,
                            is_group: values.send_group ? 1 : 0,
                            is_individual: values.send_individual ? 1 : 0,
                            group_name: values.group || null,
                            individual_name: values.individual || null,
                            multi_doc_to_pdf:values.multi_doc_to_pdf? 1:0
                        },
                        callback: function (r) {
                            if (r.message === 'Success') {
                                frappe.msgprint(__('Notifications sent successfully!'));
                            }
                        }
                    });

                    d.hide();
                }
            });

            d.show();
        }
    }
});

    });



    //  To display report
    function display_report_data(items,total_count,total_qty) {
         page.set_indicator(`Total Count: ${total_count} | Total Qty: ${total_qty}` , 'green');
        if (!items || items.length === 0) {
        $('<div>No data found</div>')
            .css({
                textAlign: 'center',
                padding: '20px',
                color: '#666',
                fontSize: '16px',
                fontStyle: 'italic'
            })
            .appendTo(grid_container);
        return;
    }

        items.forEach(function (item) {
            // Create a container with relative positioning
        let item_div = $('<div class="item-container"></div>').css({
            position: 'relative',  // <-- THIS IS IMPORTANT
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '15px',
            textAlign: 'center',
            border: '1px solid #ddd',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #e3f2fd, #fce4ec)',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            transition: 'transform 0.2s, box-shadow 0.2s',
            cursor: 'pointer',
            marginBottom: '20px'
        }).hover(
            function () {
                $(this).css({
                    transform: 'scale(1.05)',
                    boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)'
                });
            },
            function () {
                $(this).css({
                    transform: 'scale(1)',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                });
            }
        ).appendTo(grid_container);

        // ADD the Checkbox (absolute positioned)
        let checkbox = $('<input type="checkbox" class="item-checkbox">').css({
            position: 'absolute',
            top: '10px',
            left: '10px',
            transform: 'scale(1.2)',
            cursor: 'pointer'
        }).appendTo(item_div);




            // Item Image
            let img = $('<img>').attr('src', item.image || 'placeholder-image-url.png')
                .css({
                    width: '160px',
                    height: '100px',
                    objectFit: 'cover',
                    borderRadius: '8px',
                    marginBottom: '10px'
                }).appendTo(item_div);
            $('<a>')
                .attr('href', item.image || 'placeholder-image-url.png')
                .attr('target', '_blank') // Opens in a new tab
                .append(img) // Append the image inside the link
                .appendTo(item_div);

            // Item Code / Name
            $('<div></div>').text(`Item: ${item.item || 'No Item Code'}`)
                .css({
                    fontWeight: 'bold',
                    fontSize: '14px',
                    marginBottom: '8px',
                    color: '#333' // Darker text for contrast
                })
                .on('click', function() {
                    window.open(`${window.location.href.split("/app/")[0]}/app/item/${item.item}`,'_blank')
                }).appendTo(item_div);

            // Item description

            $('<div></div>').text(`Item Group: ${item.item_group || 'N/A'}`)
                .css({
                    fontSize: '12px',
                    color: '#666',
                    marginBottom: '8px'
                }).appendTo(item_div);

            // Stock Quantity
            $('<div></div>').text(`Total Qty: ${item.qty || '0'}`)
                .css({
                    fontSize: '12px',
                    color: '#333'
                }).appendTo(item_div);

        });

    }
     update_dashboard();
}