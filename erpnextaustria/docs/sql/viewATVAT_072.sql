CREATE VIEW `viewATVAT_072` AS
SELECT 
    `tabPurchase Invoice`.`posting_date` AS `posting_date`, 
    `tabPurchase Invoice`.`name` AS `name`, 
    `tabPurchase Invoice`.`base_grand_total`  AS `base_grand_total`, 
    `tabPurchase Invoice`.`base_net_total` AS `base_net_total`,
    `tabPurchase Invoice`.`taxes_and_charges` AS `taxes_and_charges`, 
    `tabPurchase Invoice`.`total_taxes_and_charges` AS `total_taxes_and_charges`
FROM `tabPurchase Invoice` 
WHERE `docstatus` = 1 AND `taxes_and_charges` LIKE '%072%'
