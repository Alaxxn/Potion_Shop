create table
  public.active_cart_item (
    id bigint generated by default as identity not null,
    cart_id integer not null,
    sku text null,
    quantity integer null,
    constraint cart_item_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.active_carts (
    id bigint generated by default as identity not null,
    customer_id integer not null,
    constraint carts_pkey primary key (id)
  ) tablespace pg_default; 

create table
  public.barrel_inventory (
    id bigint generated by default as identity not null,
    name text not null default ''::text,
    potion_type integer[] null,
    constraint barrel_inventory_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.barrel_ledger (
    id bigint generated by default as identity not null,
    potion_type integer[] null,
    change integer null,
    day text null,
    hour integer null,
    transaction_id integer null,
    order_id integer null,
    constraint barrel_ledger_pkey primary key (id),
    constraint barrel_ledger_transaction_id_fkey foreign key (transaction_id) references barrel_transactions (id)
  ) tablespace pg_default;

create table
  public.barrel_transactions (
    id integer generated by default as identity not null,
    description text null,
    constraint barrel_transactions_pkey primary key (id)
  ) tablespace pg_default;

create view
  public.current_day as
select
  days.game_day as day,
  days.game_hour as hour
from
  days
order by
  days.id desc
limit
  1;

create table
  public.customer (
    id bigint generated by default as identity not null,
    name text not null,
    class text null,
    level integer null,
    hour integer null,
    day text null,
    constraint customers_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.days (
    id bigint generated by default as identity not null,
    game_day text not null,
    game_hour integer null,
    real_time timestamp with time zone null default now(),
    constraint current_day_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.gold_ledger (
    id bigint generated by default as identity not null,
    transaction_id integer null,
    change integer not null default 0,
    day text null,
    hour integer null,
    constraint gold_ledger_pkey primary key (id),
    constraint gold_ledger_account_transaction_id_key unique (transaction_id),
    constraint gold_ledger_transaction_id_fkey foreign key (transaction_id) references gold_transactions (id)
  ) tablespace pg_default;

create table
  public.gold_transactions (
    id integer generated by default as identity not null,
    description text null,
    constraint gold_transactions_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potion_inventory (
    id bigint generated by default as identity not null,
    sku text not null,
    name text null,
    price integer null,
    in_catalog boolean null default false,
    potion_type integer[] null,
    constraint potion_type_pkey primary key (id),
    constraint potion_type_id_key unique (id)
  ) tablespace pg_default;

create table
  public.potion_ledger (
    id bigint generated by default as identity not null,
    potion_type integer[] null,
    transaction_id bigint null,
    change integer null,
    day text null,
    hour integer null,
    order_id integer null,
    constraint potion_ledger_pkey primary key (id),
    constraint potion_ledger_transaction_id_fkey foreign key (transaction_id) references potion_transactions (id)
  ) tablespace pg_default;

create table
  public.potion_transactions (
    id bigint generated by default as identity not null,
    description text null,
    constraint potion_transaction_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.purchase_history (
    id bigint generated by default as identity not null,
    name text not null,
    class text null,
    level integer null,
    potion_type integer[] null,
    day text null,
    hour integer null,
    quantity integer null,
    timestamp timestamp with time zone null default now(),
    constraint purchse_history_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.shop (
    id bigint generated by default as identity not null,
    ml_capacity integer null default 0,
    potion_capacity integer null default 0,
    constraint shop_inventory_ledger_pkey primary key (id)
  ) tablespace pg_default;