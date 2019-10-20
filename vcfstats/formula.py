from os.path import commonprefix
from collections import OrderedDict
from . import MACROS, LOGGER

def parse_subsets(subsets):
	ret = []
	for subset in subsets.split(','):
		subset = subset.strip()
		if subset.count('-') == 1:
			start, end = subset.split('-')
			compref = commonprefix([start, end])
			if compref and compref[-1].isdigit():
				compref = compref[:-1]
			start = start[len(compref):]
			end = end[len(compref):]
			if start.isdigit() and end.isdigit() and int(start) < int(end):
				ret.extend([compref + str(i) for i in range(int(start), int(end)+1)])
			else:
				ret.append(subset)
		else:
			ret.append(subset)
	return ret

class Term:

	def __init__(self, term, samples):
		token = ' \t[{'
		pos = [term.find(c) for c in token]
		if max(pos) == -1:
			remaining = ''
		else:
			pos = min(p for p in pos if p >= 0)
			term, remaining = term[:pos], term[pos:]

		if term == '1':
			term = '_ONE'
		if term not in MACROS:
			raise ValueError("Term {!r} has not been registered.".format(term))
		self.name = term if term != '_ONE' else '1'
		self.term = MACROS[term]
		if not self.term.get('type'):
			raise TypeError("No type specified for Term: {}".format(self.term))
		remaining = remaining.strip()

		errmsg = 'Malformated decorations for an Term. Expect {SAMPLE}, [SUBSETS] or a combination of both.'
		self.samples = self.subsets = None

		if not remaining:
			pass
		elif remaining[0] == '[' and remaining[-1] == ']':
			self.subsets = parse_subsets(remaining[1:-1])
		elif remaining[0] == '{' and remaining[-1] == '}':
			self.samples = parse_subsets(remaining[1:-1])
		elif remaining[0] == '{' and remaining[-1] == ']':
			if not '}[' in remaining:
				raise ValueError(errmsg)
			specified_samples, subsets = remaining[1:-1].split('}[', 1)
			self.samples = parse_subsets(specified_samples)
			self.subsets = parse_subsets(subsets)
		elif remaining[0] == '[' and remaining[-1] == '}':
			if not ']{' in remaining:
				raise ValueError(errmsg)
			subsets, specified_samples = remaining[1:-1].split(']{', 1)
			self.samples = parse_subsets(specified_samples)
			self.subsets = parse_subsets(subsets)
		else:
			raise ValueError(errmsg)

		if self.samples:
			for i, sample in enumerate(self.samples):
				if sample.isdigit():
					self.samples[i] = int(sample)
				elif sample not in samples:
					raise ValueError('Sample {!r} does not exist.'.format(sample))
				else:
					self.samples[i] = samples.index(sample)

		if self.term['type'] == 'continuous' and self.subsets:
			if len(self.subsets) != 2:
				raise KeyError('Expect a subset of length 2 for continuous Term: {}'.format(self.term))
			if self.subsets[0]:
				self.subsets[0] = float(self.subsets[0]) # try to raise
			if self.subsets[1]:
				self.subsets[1] = float(self.subsets[1])

	def __repr__(self):
		return '<Term {!r}(subsets={!r}, samples={!r})>'.format(self.name, self.subsets, self.samples)

	def __eq__(self, other):
		if not isinstance(other, Term):
			return False
		return self.term == other.term and self.subsets == other.subsets and self.samples == other.samples

	def __ne__(self, other):
		return not self.__eq__(other)

	def run(self, variant, passed):
		if passed and variant.FILTER:
			return False
		value = self.term['func'](variant)
		if value is False or value is None:
			return False
		# numpy.array
		if not hasattr(value, 'T') and not isinstance(value, (tuple,list)):
			value = [value]
		if self.samples:
			value = [value[sidx] for sidx in self.samples]

		if self.term['type'] == 'continuous' and self.subsets:
			if self.subsets[0] and any(val < self.subsets[0] for val in value):
				return False
			if self.subsets[1] and any(val > self.subsets[1] for val in value):
				return False
		if self.term['type'] == 'categorical' and self.subsets:
			if any(val not in self.subsets for val in value):
				return False
		return value

class Aggr:

	def __init__(self, aggr, terms):
		self.cache = OrderedDict() # cache data for aggregation
		aggr, remaining = aggr.split('(', 1)
		aggr = aggr.strip()
		if aggr not in MACROS or not MACROS[aggr].get('aggr'):
			raise ValueError("Aggregation {!r} has not been registered.".format(aggr))
		self.aggr = MACROS[aggr]

		remaining = remaining.strip()
		if not remaining.endswith(')'):
			raise ValueError("Expect an Aggregation in format of 'AGGR(...)'")
		remaining = remaining[:-1]
		if ',' not in remaining:
			term, remaining = remaining, ''
		else:
			term, remaining = remaining.split(',', 1)

		term = term.strip()
		remaining = remaining.strip()
		self.term = terms[term]
		self.filter = None
		self.group = None
		for term in remaining.split(','):
			term = term.strip()
			if not term:
				continue
			if '=' not in term:
				kw, name = 'filter', term
			else:
				kw, name = term.split('=')
			if kw == 'filter':
				self.filter = terms[name]
			else:
				self.group = terms[name]

		self.name = '{}({})'.format(aggr, self.term.name)
		if self.term.term['type'] != 'continuous':
			raise TypeError("Cannot aggregate on categorical data.")

		if self.group and self.group.term['type'] != 'categorical':
			raise TypeError("Cannot aggregate on continuous groups.")

		self.xgroup = None

	def __repr__(self):
		return '<Aggr {!r}({!r}, filter={!r}, group={!r})>'.format(
			self.aggr['func'].__name__, self.term, self.filter, self.group)

	def hasFILTER(self):
		return self.term.name == 'FILTER' or (self.filter and self.filter.name == 'FILTER') or \
			(self.group and self.group.name == 'FILTER')

	def setxgroup(self, x):
		if not self.group:
			self.group = x
		else:
			self.xgroup = x

	def run(self, variant, passed):
		if self.filter and self.filter.run(variant, passed) is False:
			return
		if not self.group:
			raise RuntimeError("No group specified, don't know how to aggregate.")
		group = self.group.run(variant, passed)
		if group is False:
			return
		if len(group) > 1:
			raise ValueError("Cannot aggregate on more than one group.")
		group = group[0]

		xgroup = False
		if (self.xgroup):
			xgroup = self.xgroup.run(variant, passed)
			if xgroup is False:
				return
			if len(xgroup) > 1:
				raise ValueError("Cannot aggregate on more than one xgroup.")
			xgroup = xgroup[0]

		value = self.term.run(variant, passed)

		if value is False:
			return
		if xgroup:
			self.cache.setdefault(xgroup, {}).setdefault(group, []).extend(value)
		else:
			self.cache.setdefault(group, []).extend(value)

	def dump(self):
		ret = OrderedDict()
		for key, value in self.cache.items():
			if isinstance(value, dict):
				ret[key] = [(self.aggr['func'](val), grup) for grup, val in value.items()]
			else:
				ret[key] = self.aggr['func'](value)
		del self.cache
		return ret

class Formula:

	def __init__(self, formula, samples, passed, title):
		LOGGER.info("[{}] Parsing formulas ...".format(title))
		self._terms = {}
		if '~' not in formula:
			formula = formula + '~1'
		parts = formula.split('~', 1)
		if not parts[1].strip():
			parts[1] = '1'
		LOGGER.debug('[{}] - Y:{!r}, X:{!r}'.format(title, parts[0], parts[1]))
		self.Y = self._parse_part(parts[0].strip(), samples)
		self.X = self._parse_part(parts[1].strip(), samples)
		if isinstance(self.Y, Aggr) and isinstance(self.X, Term):
			self.Y.setxgroup(self.X)
		self.passed = passed
		if  (isinstance(self.Y, Term) and self.Y.name == 'FILTER') or \
			(isinstance(self.Y, Aggr) and self.Y.hasFILTER()) or \
			(isinstance(self.X, Term) and self.X.name == 'FILTER') or \
			(isinstance(self.X, Aggr) and self.X.hasFILTER()):
			self.passed = False

	def _parse_part(self, part, samples):
		aggr = None
		if part.endswith(')'):
			aggr, term_fms = part[:-1].split('(')
		else:
			term_fms = part
		breakat = []
		bracket = False
		sqarekt = False
		for i, char in enumerate(term_fms):
			bracket = bracket if char not in '}{' else char == '{'
			sqarekt = sqarekt if char not in '][' else char == '['
			if char == ',' and not bracket and not sqarekt:
				breakat.append(i)

		if not breakat and not aggr:
			return Term(term_fms, samples)
		if not breakat and aggr:
			name = 'TERM' + str(len(self._terms))
			self._terms[name] = Term(term_fms, samples)
			return Aggr('{}({})'.format(aggr, name), self._terms)
		if len(breakat) > 2:
			raise ValueError('Wrong number of arguments (at most 3) for Aggregation: {}.'.format(aggr))

		name1 = 'TERM' + str(len(self._terms))
		self._terms[name1] = self._parse_part(term_fms[:breakat[0]], samples)
		args = [name1]
		for i, bat in enumerate(breakat):
			if i == len(breakat) - 1:
				termstr = term_fms[(bat+1):].strip()
			else:
				termstr = term_fms[(bat+1):breakat[i+1]].strip()
			kw = None
			if '=' in termstr:
				kw, termstr = termstr.split('=', 1)
				kw, termstr = kw.strip(), termstr.strip()
			kw = kw or ('filter' if i == 0 else 'group')
			if kw not in ('filter', 'group'):
				raise ValueError('Expect filter/group as keyword argument name, but got {}.'.format(kw))

			name2 = 'TERM' + str(len(self._terms))
			self._terms[name2] = self._parse_part(termstr, samples)
			args.append('{}={}'.format(kw, name2))
		print('{}({})'.format(aggr, ', '.join(args)))
		return Aggr('{}({})'.format(aggr, ', '.join(args)), self._terms)

	def run(self, variant, datafile):
		if isinstance(self.Y, Term) and isinstance(self.X, Term):
			y, x = self.Y.run(variant, self.passed), self.X.run(variant, self.passed)
			if y is False or x is False:
				return
			lenx = len(x)
			leny = len(y)
			if leny != lenx and leny != 1 and lenx != 1:
				raise RuntimeError('Unmatched length of MACRO results: Y({}), X({})'.format(leny, lenx))
			if lenx == 1:
				x = x * leny
			if leny == 1:
				y = y * lenx
			for i, r in enumerate(x):
				datafile.write('{}\t{}\n'.format(y[i], r))
		elif isinstance(self.Y, Aggr) and isinstance(self.X, Aggr):
			if not self.Y.group:
				self.Y.group = self.X.group
			if not self.X.group:
				self.X.group = self.Y.group
			if self.Y.group != self.X.group:
				raise ValueError("Two aggregations have to group by the same entry.")
			self.Y.run(variant, self.passed)
			self.X.run(variant, self.passed)
		elif isinstance(self.Y, Aggr) and isinstance(self.X, Term):
			self.Y.run(variant, self.passed)
		else:
			raise TypeError("Cannot do 'TERM ~ AGGREGATION'. If you want to do that, transpose 'AGGREGATION ~ TERM'")

	def done(self, datafile):
		if isinstance(self.Y, Aggr):
			if isinstance(self.X, Term):
				for key, value in self.Y.dump().items():
					if isinstance(value, list):
						for val, grup in value:
							datafile.write("{}\t{}\t{}\n".format(val, key, grup))
					else:
						datafile.write("{}\t{}\n".format(value, key))
			else:
				xdump = self.X.dump()
				for key, value in self.Y.dump().items():
					datafile.write("{}\t{}\t{}\n".format(value, xdump.get(key, 'NA'), key))


