

import javax.inject.Inject

import play.api.http.DefaultHttpFilters
import play.filters.headers.SecurityHeadersFilter
import play.filters.cors.CORSFilter

class Filters @Inject()(securityHeadersFilter: SecurityHeadersFilter, corsFilter: CORSFilter)  extends DefaultHttpFilters(securityHeadersFilter, corsFilter)
