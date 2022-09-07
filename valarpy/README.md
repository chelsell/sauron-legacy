# 🌴 Valarpy

Python code to talk to Valar.

Valarpy is an `ORM <https://en.wikipedia.org/wiki/Object%E2%80%93relational_mapping>`_
for Valar based on `Peewee <https://github.com/coleifer/peewee>`_.
There is more documentation available in the Valar readme.
Install sauronlab, which will install this.

## 🔨 Basic usage


Read-only:

```python
import valarpy

with valarpy.opened() as model:
	print(list(model.Refs.select()))
```

Write-access:

```python
import valarpy

with valarpy.for_write() as model:
  print(list(model.Refs.select()))
```

## Privileges

If your database username provides privileges for `INSERT`, `UPDATE`, or `DELETE`,
you can run those queries via valarpy.
Because the vast majority of access does not require modifying the database –
and mistakes can be catastrophic and require reloading from a nightly backup –
you must call `enable_write()`.

**Warning:**
Although valarpy is mostly thread-safe when using atomic transactions,
it uses a global write-access flag.
That means that if you call `enable_write` (see below), all code can write,
even if it called `valarpy.opened()` separately.

You should use `transactions <https://mariadb.com/kb/en/start-transaction/>`_
and/or `savepoints <https://mariadb.com/kb/en/savepoint/>`_.
In the following code, an atomic transaction is started, and the transaction is committed
when the context manager closes. If an exception is raised within the transaction block,
it will be automatically rolled back on exit.

```python
import valarpy

with valarpy.opened() as model:
	model.conn.backend.enable_write()
	with model.atomic():
		ref = Refs.fetch(1)
		ref.name = "modified-name"
		ref.save()
	# transaction is now committed
```

If you nest `atomic()` calls, the nested call(s) will create savepoints rather than initiate new transactions.
If a transaction fails in the nested block, it will be rolled back to the savepoint:

```python
import valarpy
with valarpy.opened() as model:
	# enable write access
	model.conn.backend.enable_write()
	# This starts a transaction:
	with model.conn.atomic():
		ref = Refs.fetch(1)
		ref.name = "improved-name"
		ref.version = "version 2"
		try:
			# This just creates a savepoint
			with model.conn.atomic():
				ref.name = "name modified again"
				ref.save()
				raise ValueError("Fail!")
			# savepoint exits
		except:
			print("Rolling back to checkpoint")
			# prints "name=improved-name, version="version 2"
			print(f"name={ref.name}, version={ref.version}")
	# transaction is now committed
```

You would never nest `atomic` calls in a single function, but you might call a function that also calls `atomic`.
There is a method analogous to `atomic` called `rolling_back`. This will roll back to the transaction
or savepoint when the block closes, whether or not an exception was called. This is especially useful when writing tests.
Finally, `model.atomic()` and `model.rolling_back()` both yield a Transaction object that has several methods,
including `.commit()` and `.rollback()`. In general, you would not want to call these directly, but you can.
