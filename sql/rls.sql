ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_orders" ON public.orders
    FOR SELECT
    TO anon
    USING (true);

ALTER TABLE public.order_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_order_items" ON public.order_items
    FOR SELECT
    TO anon
    USING (true);

ALTER TABLE public.customers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_customers" ON public.customers
    FOR SELECT
    TO anon
    USING (true);

ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_products" ON public.products
    FOR SELECT
    TO anon
    USING (true);

ALTER TABLE public.sellers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_sellers" ON public.sellers
    FOR SELECT
    TO anon
    USING (true);

ALTER TABLE public.order_reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_order_reviews" ON public.order_reviews
    FOR SELECT
    TO anon
    USING (true);

ALTER TABLE public.order_payments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public_read_order_payments" ON public.order_payments
    FOR SELECT
    TO anon
    USING (true);