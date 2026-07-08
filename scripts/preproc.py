# %%
import pandas as pd

# %%
orders = pd.read_csv('data/raw/olist_orders_dataset.csv')

# %% [markdown]
# Miramos la cantidad de ordenes por mes

# %%
orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
orders['order_month'] = orders['order_purchase_timestamp'].dt.to_period('M')
orders_per_month = orders.groupby('order_month').size().reset_index(name='orders_count')

# %%
orders_per_month

# %% [markdown]
# El dataset es inconsistente antes del 2017 y despues de Agosto del 2018.
# 
# Filtramos por estas fechas y guardamos en ``data/proc``

# %%
orders_filtered = orders[
    (orders['order_purchase_timestamp'] >= '2017-01-01') &
    (orders['order_purchase_timestamp'] < '2018-09-01')
]
orders_filtered['order_month'] = orders_filtered['order_purchase_timestamp'].dt.to_period('M')
orders_per_month_filtered = orders_filtered.groupby('order_month').size().reset_index(name='orders_count')
orders_per_month_filtered

# %%
valid_order_ids = set(orders_filtered['order_id'])

# %%
order_payments = pd.read_csv('data/raw/olist_order_payments_dataset.csv')
order_items = pd.read_csv('data/raw/olist_order_items_dataset.csv')
order_reviews = pd.read_csv('data/raw/olist_order_reviews_dataset.csv')

# %%
order_payments_filtered = order_payments[order_payments['order_id'].isin(valid_order_ids)]
order_items_filtered   = order_items[order_items['order_id'].isin(valid_order_ids)]
order_reviews_filtered = order_reviews[order_reviews['order_id'].isin(valid_order_ids)]

# %%
orders_filtered.drop(columns=['order_month'], inplace=True)
orders_filtered.to_csv('data/proc/olist_orders_dataset.csv', index=False)

# %%
order_payments_filtered.to_csv('data/proc/olist_order_payments_dataset.csv', index=False)
order_items_filtered.to_csv('data/proc/olist_order_items_dataset.csv', index=False)
order_reviews_filtered.to_csv('data/proc/olist_order_reviews_dataset.csv', index=False)


