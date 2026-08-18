"""Chinook benchmark question definitions (lowercase Postgres schema)."""

from __future__ import annotations

from typing import Any, TypedDict


class QuestionSpec(TypedDict, total=False):
    id: str
    dataset: str
    category: str
    question: str
    reference_sql: str
    ignore_order: bool


BENCHMARK_QUESTIONS: list[QuestionSpec] = [
    # --- Single-table filter/count (20) ---
    {
        "id": "cq001",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many customers are from Brazil?",
        "reference_sql": "SELECT COUNT(*) FROM customer WHERE country = 'Brazil'",
    },
    {
        "id": "cq002",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many customers are there in total?",
        "reference_sql": "SELECT COUNT(*) FROM customer",
    },
    {
        "id": "cq003",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many customers are from the USA?",
        "reference_sql": "SELECT COUNT(*) FROM customer WHERE country = 'USA'",
    },
    {
        "id": "cq004",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many music genres are in the database?",
        "reference_sql": "SELECT COUNT(*) FROM genre",
    },
    {
        "id": "cq005",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many employees are there?",
        "reference_sql": "SELECT COUNT(*) FROM employee",
    },
    {
        "id": "cq006",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many invoices exist?",
        "reference_sql": "SELECT COUNT(*) FROM invoice",
    },
    {
        "id": "cq007",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many tracks are in the database?",
        "reference_sql": "SELECT COUNT(*) FROM track",
    },
    {
        "id": "cq008",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many albums are there?",
        "reference_sql": "SELECT COUNT(*) FROM album",
    },
    {
        "id": "cq009",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many artists are in the database?",
        "reference_sql": "SELECT COUNT(*) FROM artist",
    },
    {
        "id": "cq010",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many tracks are longer than 5 minutes?",
        "reference_sql": "SELECT COUNT(*) FROM track WHERE milliseconds > 300000",
    },
    {
        "id": "cq011",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many playlists are there?",
        "reference_sql": "SELECT COUNT(*) FROM playlist",
    },
    {
        "id": "cq012",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many media types exist?",
        "reference_sql": "SELECT COUNT(*) FROM media_type",
    },
    {
        "id": "cq013",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many invoice line items are there?",
        "reference_sql": "SELECT COUNT(*) FROM invoice_line",
    },
    {
        "id": "cq014",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many customers are from Canada?",
        "reference_sql": "SELECT COUNT(*) FROM customer WHERE country = 'Canada'",
    },
    {
        "id": "cq015",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many customers are from Germany?",
        "reference_sql": "SELECT COUNT(*) FROM customer WHERE country = 'Germany'",
    },
    {
        "id": "cq016",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many tracks have a unit price greater than 1?",
        "reference_sql": "SELECT COUNT(*) FROM track WHERE unit_price > 1",
    },
    {
        "id": "cq017",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many albums does artist id 1 have?",
        "reference_sql": "SELECT COUNT(*) FROM album WHERE artist_id = 1",
    },
    {
        "id": "cq018",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many invoices were issued in 2021?",
        "reference_sql": (
            "SELECT COUNT(*) FROM invoice "
            "WHERE invoice_date >= DATE '2021-01-01' AND invoice_date < DATE '2022-01-01'"
        ),
    },
    {
        "id": "cq019",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many customers live in Calgary?",
        "reference_sql": "SELECT COUNT(*) FROM customer WHERE city = 'Calgary'",
    },
    {
        "id": "cq020",
        "dataset": "chinook",
        "category": "filter",
        "question": "How many tracks are shorter than one minute?",
        "reference_sql": "SELECT COUNT(*) FROM track WHERE milliseconds < 60000",
    },
    # --- Joins (30) ---
    {
        "id": "cq021",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 customer first names with their support representative last name",
        "reference_sql": (
            "SELECT c.first_name, e.last_name "
            "FROM customer c JOIN employee e ON c.support_rep_id = e.employee_id "
            "ORDER BY c.customer_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq022",
        "dataset": "chinook",
        "category": "join",
        "question": "Show 10 track names with their album titles",
        "reference_sql": (
            "SELECT t.name AS track_name, al.title AS album_title "
            "FROM track t JOIN album al ON t.album_id = al.album_id "
            "ORDER BY t.track_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq023",
        "dataset": "chinook",
        "category": "join",
        "question": "Show 10 artist names with album titles",
        "reference_sql": (
            "SELECT ar.name AS artist_name, al.title AS album_title "
            "FROM artist ar JOIN album al ON ar.artist_id = al.artist_id "
            "ORDER BY ar.artist_id, al.album_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq024",
        "dataset": "chinook",
        "category": "join",
        "question": "Show 10 invoice totals with customer last names",
        "reference_sql": (
            "SELECT i.total, c.last_name "
            "FROM invoice i JOIN customer c ON i.customer_id = c.customer_id "
            "ORDER BY i.invoice_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq025",
        "dataset": "chinook",
        "category": "join",
        "question": "How many tracks does each genre have?",
        "reference_sql": (
            "SELECT g.name, COUNT(*) AS track_count "
            "FROM genre g JOIN track t ON g.genre_id = t.genre_id "
            "GROUP BY g.name"
        ),
    },
    {
        "id": "cq026",
        "dataset": "chinook",
        "category": "join",
        "question": "List customer company names with their support rep first name (limit 10)",
        "reference_sql": (
            "SELECT c.company, e.first_name "
            "FROM customer c JOIN employee e ON c.support_rep_id = e.employee_id "
            "WHERE c.company IS NOT NULL "
            "ORDER BY c.customer_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq027",
        "dataset": "chinook",
        "category": "join",
        "question": "Show playlist names with how many tracks each contains",
        "reference_sql": (
            "SELECT p.name, COUNT(pt.track_id) AS track_count "
            "FROM playlist p LEFT JOIN playlist_track pt ON p.playlist_id = pt.playlist_id "
            "GROUP BY p.name"
        ),
    },
    {
        "id": "cq028",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 tracks with their media type name",
        "reference_sql": (
            "SELECT t.name, m.name AS media_type "
            "FROM track t JOIN media_type m ON t.media_type_id = m.media_type_id "
            "ORDER BY t.track_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq029",
        "dataset": "chinook",
        "category": "join",
        "question": "How many albums does each artist have?",
        "reference_sql": (
            "SELECT ar.name, COUNT(*) AS album_count "
            "FROM artist ar JOIN album al ON ar.artist_id = al.artist_id "
            "GROUP BY ar.name"
        ),
    },
    {
        "id": "cq030",
        "dataset": "chinook",
        "category": "join",
        "question": "Show 10 invoice line quantities with track names",
        "reference_sql": (
            "SELECT il.quantity, t.name "
            "FROM invoice_line il JOIN track t ON il.track_id = t.track_id "
            "ORDER BY il.invoice_line_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq031",
        "dataset": "chinook",
        "category": "join",
        "question": "Which countries have customers and how many customers per country?",
        "reference_sql": "SELECT country, COUNT(*) AS customer_count FROM customer GROUP BY country",
    },
    {
        "id": "cq032",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 albums with their artist names",
        "reference_sql": (
            "SELECT al.title, ar.name AS artist_name "
            "FROM album al JOIN artist ar ON al.artist_id = ar.artist_id "
            "ORDER BY al.album_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq033",
        "dataset": "chinook",
        "category": "join",
        "question": "Show total invoice amount per customer country",
        "reference_sql": (
            "SELECT c.country, SUM(i.total) AS total_sales "
            "FROM customer c JOIN invoice i ON c.customer_id = i.customer_id "
            "GROUP BY c.country"
        ),
    },
    {
        "id": "cq034",
        "dataset": "chinook",
        "category": "join",
        "question": "How many tracks are on each album?",
        "reference_sql": (
            "SELECT al.title, COUNT(*) AS track_count "
            "FROM album al JOIN track t ON al.album_id = t.album_id "
            "GROUP BY al.title"
        ),
    },
    {
        "id": "cq035",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 customers with their city and support rep last name",
        "reference_sql": (
            "SELECT c.first_name, c.city, e.last_name "
            "FROM customer c JOIN employee e ON c.support_rep_id = e.employee_id "
            "ORDER BY c.customer_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq036",
        "dataset": "chinook",
        "category": "join",
        "question": "What is the average track length in milliseconds for each genre?",
        "reference_sql": (
            "SELECT g.name, AVG(t.milliseconds) AS avg_ms "
            "FROM genre g JOIN track t ON g.genre_id = t.genre_id "
            "GROUP BY g.name"
        ),
    },
    {
        "id": "cq037",
        "dataset": "chinook",
        "category": "join",
        "question": "Show 10 invoice dates with customer first names",
        "reference_sql": (
            "SELECT i.invoice_date, c.first_name "
            "FROM invoice i JOIN customer c ON i.customer_id = c.customer_id "
            "ORDER BY i.invoice_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq038",
        "dataset": "chinook",
        "category": "join",
        "question": "How many invoice lines does each invoice have?",
        "reference_sql": (
            "SELECT i.invoice_id, COUNT(*) AS line_count "
            "FROM invoice i JOIN invoice_line il ON i.invoice_id = il.invoice_id "
            "GROUP BY i.invoice_id"
        ),
    },
    {
        "id": "cq039",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 tracks with genre name and unit price",
        "reference_sql": (
            "SELECT t.name, g.name AS genre, t.unit_price "
            "FROM track t JOIN genre g ON t.genre_id = g.genre_id "
            "ORDER BY t.track_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq040",
        "dataset": "chinook",
        "category": "join",
        "question": "What is the total revenue per employee based on invoices for their customers?",
        "reference_sql": (
            "SELECT e.last_name, SUM(i.total) AS total_sales "
            "FROM employee e "
            "JOIN customer c ON c.support_rep_id = e.employee_id "
            "JOIN invoice i ON i.customer_id = c.customer_id "
            "GROUP BY e.last_name"
        ),
    },
    {
        "id": "cq041",
        "dataset": "chinook",
        "category": "join",
        "question": "Show 10 composers with their track names where composer is not null",
        "reference_sql": (
            "SELECT t.composer, t.name "
            "FROM track t "
            "WHERE t.composer IS NOT NULL "
            "ORDER BY t.track_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq042",
        "dataset": "chinook",
        "category": "join",
        "question": "How many customers does each employee support?",
        "reference_sql": (
            "SELECT e.first_name, e.last_name, COUNT(*) AS customer_count "
            "FROM employee e JOIN customer c ON c.support_rep_id = e.employee_id "
            "GROUP BY e.first_name, e.last_name"
        ),
    },
    {
        "id": "cq043",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 tracks with album title and artist name",
        "reference_sql": (
            "SELECT t.name AS track_name, al.title AS album_title, ar.name AS artist_name "
            "FROM track t "
            "JOIN album al ON t.album_id = al.album_id "
            "JOIN artist ar ON al.artist_id = ar.artist_id "
            "ORDER BY t.track_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq044",
        "dataset": "chinook",
        "category": "join",
        "question": "What is the total quantity sold per track?",
        "reference_sql": (
            "SELECT t.name, SUM(il.quantity) AS total_quantity "
            "FROM track t JOIN invoice_line il ON t.track_id = il.track_id "
            "GROUP BY t.name"
        ),
    },
    {
        "id": "cq045",
        "dataset": "chinook",
        "category": "join",
        "question": "Show billing country and total invoice amount grouped by billing country",
        "reference_sql": (
            "SELECT billing_country, SUM(total) AS total_amount FROM invoice GROUP BY billing_country"
        ),
    },
    {
        "id": "cq046",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 customers with their total number of invoices",
        "reference_sql": (
            "SELECT c.first_name, c.last_name, COUNT(i.invoice_id) AS invoice_count "
            "FROM customer c JOIN invoice i ON c.customer_id = i.customer_id "
            "GROUP BY c.first_name, c.last_name "
            "ORDER BY invoice_count DESC LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq047",
        "dataset": "chinook",
        "category": "join",
        "question": "How many tracks use each media type?",
        "reference_sql": (
            "SELECT m.name, COUNT(*) AS track_count "
            "FROM media_type m JOIN track t ON m.media_type_id = t.media_type_id "
            "GROUP BY m.name"
        ),
    },
    {
        "id": "cq048",
        "dataset": "chinook",
        "category": "join",
        "question": "Show average unit price per genre",
        "reference_sql": (
            "SELECT g.name, AVG(t.unit_price) AS avg_price "
            "FROM genre g JOIN track t ON g.genre_id = t.genre_id "
            "GROUP BY g.name"
        ),
    },
    {
        "id": "cq049",
        "dataset": "chinook",
        "category": "join",
        "question": "List 10 invoice line unit prices with track names",
        "reference_sql": (
            "SELECT il.unit_price, t.name "
            "FROM invoice_line il JOIN track t ON il.track_id = t.track_id "
            "ORDER BY il.invoice_line_id LIMIT 10"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq050",
        "dataset": "chinook",
        "category": "join",
        "question": "What is the total sales amount per city for customers?",
        "reference_sql": (
            "SELECT c.city, SUM(i.total) AS total_sales "
            "FROM customer c JOIN invoice i ON c.customer_id = i.customer_id "
            "GROUP BY c.city"
        ),
    },
    # --- Aggregations / GROUP BY (25) ---
    {
        "id": "cq051",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the total revenue from all invoices?",
        "reference_sql": "SELECT ROUND(SUM(total)::numeric, 2) AS total_revenue FROM invoice",
    },
    {
        "id": "cq052",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the average invoice total?",
        "reference_sql": "SELECT ROUND(AVG(total)::numeric, 2) AS avg_invoice_total FROM invoice",
    },
    {
        "id": "cq053",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the minimum and maximum invoice total?",
        "reference_sql": "SELECT MIN(total) AS min_total, MAX(total) AS max_total FROM invoice",
    },
    {
        "id": "cq054",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the average track unit price?",
        "reference_sql": "SELECT ROUND(AVG(unit_price)::numeric, 2) AS avg_unit_price FROM track",
    },
    {
        "id": "cq055",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the total quantity sold across all invoice lines?",
        "reference_sql": "SELECT SUM(quantity) AS total_quantity FROM invoice_line",
    },
    {
        "id": "cq056",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many customers are in each state in the USA?",
        "reference_sql": (
            "SELECT state, COUNT(*) AS customer_count "
            "FROM customer WHERE country = 'USA' GROUP BY state"
        ),
    },
    {
        "id": "cq057",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the average album length in tracks per artist (artists with albums)?",
        "reference_sql": (
            "SELECT ar.name, AVG(album_counts.cnt) AS avg_albums "
            "FROM artist ar "
            "JOIN (SELECT artist_id, COUNT(*) AS cnt FROM album GROUP BY artist_id) album_counts "
            "ON ar.artist_id = album_counts.artist_id "
            "GROUP BY ar.name"
        ),
    },
    {
        "id": "cq058",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the total billing amount per year from invoices?",
        "reference_sql": (
            "SELECT EXTRACT(YEAR FROM invoice_date)::int AS invoice_year, SUM(total) AS yearly_total "
            "FROM invoice GROUP BY EXTRACT(YEAR FROM invoice_date)"
        ),
    },
    {
        "id": "cq059",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many tracks have a null composer?",
        "reference_sql": "SELECT COUNT(*) FROM track WHERE composer IS NULL",
    },
    {
        "id": "cq060",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the average milliseconds length of all tracks?",
        "reference_sql": "SELECT ROUND(AVG(milliseconds)::numeric, 2) AS avg_ms FROM track",
    },
    {
        "id": "cq061",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many distinct customer countries are there?",
        "reference_sql": "SELECT COUNT(DISTINCT country) FROM customer",
    },
    {
        "id": "cq062",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the total unit price sum for all tracks?",
        "reference_sql": "SELECT ROUND(SUM(unit_price)::numeric, 2) AS total_unit_price FROM track",
    },
    {
        "id": "cq063",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many invoices does each billing country have?",
        "reference_sql": (
            "SELECT billing_country, COUNT(*) AS invoice_count FROM invoice GROUP BY billing_country"
        ),
    },
    {
        "id": "cq064",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the max track unit price?",
        "reference_sql": "SELECT MAX(unit_price) AS max_unit_price FROM track",
    },
    {
        "id": "cq065",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the min track unit price?",
        "reference_sql": "SELECT MIN(unit_price) AS min_unit_price FROM track",
    },
    {
        "id": "cq066",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many customers have a company name filled in?",
        "reference_sql": "SELECT COUNT(*) FROM customer WHERE company IS NOT NULL AND company <> ''",
    },
    {
        "id": "cq067",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the average number of tracks per album?",
        "reference_sql": (
            "SELECT ROUND(AVG(track_counts.cnt)::numeric, 2) AS avg_tracks_per_album "
            "FROM (SELECT album_id, COUNT(*) AS cnt FROM track GROUP BY album_id) track_counts"
        ),
    },
    {
        "id": "cq068",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the total invoice line amount (quantity times unit price)?",
        "reference_sql": (
            "SELECT ROUND(SUM(quantity * unit_price)::numeric, 2) AS line_total FROM invoice_line"
        ),
    },
    {
        "id": "cq069",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many albums were released per artist (count albums grouped by artist id)?",
        "reference_sql": "SELECT artist_id, COUNT(*) AS album_count FROM album GROUP BY artist_id",
    },
    {
        "id": "cq070",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the sum of invoice totals for customers in Brazil?",
        "reference_sql": (
            "SELECT ROUND(SUM(i.total)::numeric, 2) AS total_sales "
            "FROM invoice i JOIN customer c ON i.customer_id = c.customer_id "
            "WHERE c.country = 'Brazil'"
        ),
    },
    {
        "id": "cq071",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many tracks per media type id?",
        "reference_sql": "SELECT media_type_id, COUNT(*) AS track_count FROM track GROUP BY media_type_id",
    },
    {
        "id": "cq072",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the average invoice total per billing country?",
        "reference_sql": (
            "SELECT billing_country, ROUND(AVG(total)::numeric, 2) AS avg_total "
            "FROM invoice GROUP BY billing_country"
        ),
    },
    {
        "id": "cq073",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "How many playlist tracks entries exist in total?",
        "reference_sql": "SELECT COUNT(*) FROM playlist_track",
    },
    {
        "id": "cq074",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the count of customers per support rep id?",
        "reference_sql": (
            "SELECT support_rep_id, COUNT(*) AS customer_count FROM customer GROUP BY support_rep_id"
        ),
    },
    {
        "id": "cq075",
        "dataset": "chinook",
        "category": "aggregation",
        "question": "What is the total milliseconds of all tracks combined?",
        "reference_sql": "SELECT SUM(milliseconds) AS total_ms FROM track",
    },
    # --- Top-N / ORDER BY (15) ---
    {
        "id": "cq076",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 artists by number of albums",
        "reference_sql": (
            "SELECT ar.name, COUNT(*) AS album_count "
            "FROM artist ar JOIN album al ON ar.artist_id = al.artist_id "
            "GROUP BY ar.name ORDER BY album_count DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq077",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 most expensive tracks by unit price",
        "reference_sql": (
            "SELECT name, unit_price FROM track ORDER BY unit_price DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq078",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 customers by total invoice amount",
        "reference_sql": (
            "SELECT c.first_name, c.last_name, SUM(i.total) AS total_spent "
            "FROM customer c JOIN invoice i ON c.customer_id = i.customer_id "
            "GROUP BY c.first_name, c.last_name ORDER BY total_spent DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq079",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 longest tracks by milliseconds",
        "reference_sql": (
            "SELECT name, milliseconds FROM track ORDER BY milliseconds DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq080",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 genres by track count",
        "reference_sql": (
            "SELECT g.name, COUNT(*) AS track_count "
            "FROM genre g JOIN track t ON g.genre_id = t.genre_id "
            "GROUP BY g.name ORDER BY track_count DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq081",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 countries by number of customers",
        "reference_sql": (
            "SELECT country, COUNT(*) AS customer_count "
            "FROM customer GROUP BY country ORDER BY customer_count DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq082",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 albums by number of tracks",
        "reference_sql": (
            "SELECT al.title, COUNT(*) AS track_count "
            "FROM album al JOIN track t ON al.album_id = t.album_id "
            "GROUP BY al.title ORDER BY track_count DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq083",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 employees by number of supported customers",
        "reference_sql": (
            "SELECT e.first_name, e.last_name, COUNT(*) AS customer_count "
            "FROM employee e JOIN customer c ON c.support_rep_id = e.employee_id "
            "GROUP BY e.first_name, e.last_name ORDER BY customer_count DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq084",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 billing countries by total invoice revenue",
        "reference_sql": (
            "SELECT billing_country, SUM(total) AS total_revenue "
            "FROM invoice GROUP BY billing_country ORDER BY total_revenue DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq085",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 cheapest tracks by unit price",
        "reference_sql": (
            "SELECT name, unit_price FROM track ORDER BY unit_price ASC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq086",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 playlists by number of tracks",
        "reference_sql": (
            "SELECT p.name, COUNT(pt.track_id) AS track_count "
            "FROM playlist p JOIN playlist_track pt ON p.playlist_id = pt.playlist_id "
            "GROUP BY p.name ORDER BY track_count DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq087",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 customers with the most invoices",
        "reference_sql": (
            "SELECT c.first_name, c.last_name, COUNT(i.invoice_id) AS invoice_count "
            "FROM customer c JOIN invoice i ON c.customer_id = i.customer_id "
            "GROUP BY c.first_name, c.last_name ORDER BY invoice_count DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq088",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 tracks by total quantity sold",
        "reference_sql": (
            "SELECT t.name, SUM(il.quantity) AS total_quantity "
            "FROM track t JOIN invoice_line il ON t.track_id = il.track_id "
            "GROUP BY t.name ORDER BY total_quantity DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq089",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 shortest tracks by milliseconds",
        "reference_sql": (
            "SELECT name, milliseconds FROM track ORDER BY milliseconds ASC LIMIT 5"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq090",
        "dataset": "chinook",
        "category": "topn",
        "question": "Top 5 years by total invoice revenue",
        "reference_sql": (
            "SELECT EXTRACT(YEAR FROM invoice_date)::int AS invoice_year, SUM(total) AS total_revenue "
            "FROM invoice GROUP BY EXTRACT(YEAR FROM invoice_date) "
            "ORDER BY total_revenue DESC LIMIT 5"
        ),
        "ignore_order": False,
    },
    # --- Multi-hop / tricky (10) ---
    {
        "id": "cq091",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which employee supports the most customers?",
        "reference_sql": (
            "SELECT e.first_name, e.last_name, COUNT(*) AS customer_count "
            "FROM employee e JOIN customer c ON c.support_rep_id = e.employee_id "
            "GROUP BY e.first_name, e.last_name "
            "ORDER BY customer_count DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq092",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which country has the most customers?",
        "reference_sql": (
            "SELECT country, COUNT(*) AS customer_count "
            "FROM customer GROUP BY country ORDER BY customer_count DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq093",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which artist has the most albums?",
        "reference_sql": (
            "SELECT ar.name, COUNT(*) AS album_count "
            "FROM artist ar JOIN album al ON ar.artist_id = al.artist_id "
            "GROUP BY ar.name ORDER BY album_count DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq094",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which genre has the most tracks?",
        "reference_sql": (
            "SELECT g.name, COUNT(*) AS track_count "
            "FROM genre g JOIN track t ON g.genre_id = t.genre_id "
            "GROUP BY g.name ORDER BY track_count DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq095",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which customer spent the most in total across all invoices?",
        "reference_sql": (
            "SELECT c.first_name, c.last_name, SUM(i.total) AS total_spent "
            "FROM customer c JOIN invoice i ON c.customer_id = i.customer_id "
            "GROUP BY c.first_name, c.last_name ORDER BY total_spent DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq096",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which track has the highest unit price?",
        "reference_sql": (
            "SELECT name, unit_price FROM track ORDER BY unit_price DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq097",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which album has the most tracks?",
        "reference_sql": (
            "SELECT al.title, COUNT(*) AS track_count "
            "FROM album al JOIN track t ON al.album_id = t.album_id "
            "GROUP BY al.title ORDER BY track_count DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq098",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which billing country generated the most invoice revenue?",
        "reference_sql": (
            "SELECT billing_country, SUM(total) AS total_revenue "
            "FROM invoice GROUP BY billing_country ORDER BY total_revenue DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq099",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which employee generated the most invoice revenue through their customers?",
        "reference_sql": (
            "SELECT e.first_name, e.last_name, SUM(i.total) AS total_sales "
            "FROM employee e "
            "JOIN customer c ON c.support_rep_id = e.employee_id "
            "JOIN invoice i ON i.customer_id = c.customer_id "
            "GROUP BY e.first_name, e.last_name ORDER BY total_sales DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
    {
        "id": "cq100",
        "dataset": "chinook",
        "category": "tricky",
        "question": "Which track was sold the most by total quantity across invoice lines?",
        "reference_sql": (
            "SELECT t.name, SUM(il.quantity) AS total_quantity "
            "FROM track t JOIN invoice_line il ON t.track_id = il.track_id "
            "GROUP BY t.name ORDER BY total_quantity DESC LIMIT 1"
        ),
        "ignore_order": False,
    },
]

GOLDEN_QUESTION_IDS = [f"cq{i:03d}" for i in range(1, 21)]

DATASET_VERSION = "chinook-pg-v1"


def golden_questions() -> list[QuestionSpec]:
    by_id = {item["id"]: item for item in BENCHMARK_QUESTIONS}
    return [by_id[qid] for qid in GOLDEN_QUESTION_IDS]


def question_to_json(item: QuestionSpec) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item["id"],
        "dataset": item.get("dataset", "chinook"),
        "category": item["category"],
        "question": item["question"],
        "reference_sql": item["reference_sql"],
    }
    if item.get("ignore_order") is False:
        payload["ignore_order"] = False
    return payload
