# PySMTEmail

### Along the same lines as [pysmtreader](https://github.com/scadaguru/pysmtreader), this is meant to grab the data from Smart Meter Texas.  But uses a completely different mechanism.

### The reason you might want to use this instead of the already existing pysmtreader is that this should be _slightly_ less fragile.  This is through no fault of pysmtreader.  Calling the the SMT API _finicky_ would be kind.

### The other reason you might want to use this would be to get higher resolution.  Via the API you're basically stuck with 1hr resolution.  This allows 15m resolution.

## Downsides

### The primary downside is that you have to wait until end-of-day to get your data.  This also complicates something like a metric exporter because prometheus doesn't really want to deal with included timestamps.  This is a problem on the todo list.

## SQL
### Currently this inserts into a table in an MSSQL Server.  I also need to throw together a script to generate this database and table.  Eventually I hope to create an exporter or some other solution to get this into Prometheus.  There is much work to do.

## Grafana
### I have included a basic grafana dashboard to view this once you have it in SQL.
# Disclaimer.  As of writing this is currently still very very new.  You will need to get your own API key authorized for your gmail account, [this page](https://developers.google.com/gmail/api/quickstart/python) should give you all the steps you need to get started of you're really insistent on doing it _now_.