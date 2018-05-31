alter table declared_good add box_code varchar(20),
    add modify_strategy varchar(20);

alter table purchases add status varchar(20);
alter table purchase_items add custom_item_uid integer; 
