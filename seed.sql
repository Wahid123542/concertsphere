INSERT INTO Artist (ArtistName, Genre) VALUES
('Taylor Swift', 'Pop'),
('Drake', 'Hip-Hop'),
('Coldplay', 'Rock');

INSERT INTO Customer (CustomerName) VALUES
('Alice Johnson'),
('Bob Smith'),
('Carlos Martinez');

INSERT INTO Concert (VenueName, City, ConcertDate, ArtistId) VALUES
('United Center', 'Chicago', '2026-05-10', 1),
('Madison Square Garden', 'New York', '2026-06-15', 2),
('Hollywood Bowl', 'Los Angeles', '2026-07-20', 3);

INSERT INTO Orders (CustomerId, OrderDate, PaymentMethod) VALUES
(1, '2026-04-10', 'Credit Card'),
(2, '2026-04-11', 'Debit Card'),
(3, '2026-04-12', 'Cash');

INSERT INTO Ticket (ConcertId, OrderId, SeatNumber, Price) VALUES
(1, 1, 'A101', 120.00),
(2, 2, 'B205', 95.00),
(3, 3, 'C310', 150.00);