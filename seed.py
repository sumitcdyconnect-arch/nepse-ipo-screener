from app import app, db, IPO

with app.app_context():
    IPO.query.delete()
    db.session.add(IPO(name="Arun Valley Hydropower", sector="Hydropower", rating="BBB+", is_good=True, reason="Profitable 3 years in a row"))
    db.session.add(IPO(name="Nepal Textile Ltd", sector="Manufacturing", rating="BB-", is_good=False, reason="Losses reported last 2 years"))
    db.session.add(IPO(name="Himalayan Insurance", sector="Insurance", rating="A-", is_good=True, reason="Strong rating, consistent dividends"))
    db.session.commit()
    print("Done!")