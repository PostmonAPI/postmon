import pymongo

class MongoDb(object):

	_fields = [
		'logradouro',
		'bairro',
		'cidade',
		'estado',
		'complemento'
	]

	def __init__(self, address='localhost'):
		self._client = pymongo.MongoClient(address)
		self._db = self._client.postmon

	def get_one(self, cep, **kwargs):
		return self._db.ceps.find_one({ 'cep': cep }, **kwargs)

	def insert_or_update(self, obj, **kwargs):

		update = { '$set': obj }
		empty_fields = set(self._fields) - set(obj)
		update['$unset'] = dict((x, 1) for x in empty_fields)

		self._db.ceps.update({ 'cep': obj['cep'] }, update, upsert=True)

	def remove(self, cep):
		self._db.ceps.remove({ 'cep': cep })
