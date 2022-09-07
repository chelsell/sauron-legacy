/*
Taken almost entirely from https://gist.github.com/agea/6591881
The author is Andrea Agili

To run, you'll need mysql-connector on the classpath
*/

import groovy.sql.*

def env = System.getenv()

def tables = [:]

def visitTable = { dbmd, schema, tableName ->
	if (!tables[tableName]) {
		tables[tableName] = new HashSet()
	}
	def keyRS = dbmd.getExportedKeys(null, schema, tableName)
	while (keyRS.next()) {
		tables[tableName] << keyRS.getString("FKTABLE_NAME")
	}
	keyRS.close()
}

def config = [
	host: "localhost", port: 3306,
	dbname: "valar", username: env['VALAR_USER'], password: env['VALAR_PASSWORD'],
	driver: "com.mysql.jdbc.Driver",
	schema: "valar"
]
// we don't care about the timezone, so set it to UTC
def url = "jdbc:mysql://${config.host}/${config.dbname}?serverTimezone=UTC"

def sql = Sql.newInstance(url, config.username, config.password, config.driver)
def dbmd = sql.connection.metaData

def tableRS = dbmd.getTables(null, config.schema, null, "TABLE")
while (tableRS.next()) {
	visitTable(dbmd, config.schema, tableRS.getString("TABLE_NAME"))
	System.err.print "."
}
System.err.println ""
tableRS.close()

sql.connection.close()

println """
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns/graphml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:y="http://www.yworks.com/xml/graphml" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns/graphml http://www.yworks.com/xml/schema/graphml/1.0/ygraphml.xsd">
  <key for="node" id="d0" yfiles.type="nodegraphics"/>
  <key attr.name="description" attr.type="string" for="node" id="d1"/>
  <key for="edge" id="d2" yfiles.type="edgegraphics"/>
  <key attr.name="description" attr.type="string" for="edge" id="d3"/>
  <key for="graphml" id="d4" yfiles.type="resources"/>
  <graph id="${config.schema}" edgedefault="directed">
"""

tables.each { k,v ->
	nodeId = "${config.schema}_${k}"
	println """
<node id="${nodeId}">
<data key="d0">
<y:ShapeNode>
<y:Geometry height="30.0" width="${nodeId.length() * 8}.0" x="0.0" y="0.0"/>
<y:Fill color="#E8EEF7" color2="#B7C9E3" transparent="false"/>
<y:BorderStyle color="#000000" type="line" width="1.0"/>
<y:NodeLabel alignment="center" autoSizePolicy="content" fontFamily="Dialog" fontSize="13" fontStyle="plain" hasBackgroundColor="false" hasLineColor="false" height="19.92626953125" modelName="internal" modelPosition="c" textColor="#000000" visible="true" width="37.0" x="5.5" y="5.036865234375">${k}</y:NodeLabel>
<y:Shape type="rectangle"/>
<y:DropShadow color="#B3A691" offsetX="2" offsetY="2"/>
</y:ShapeNode>
</data>
</node>
"""
}

tables.each { k,v ->
	v.each { referer ->
		edgeId = "${config.schema}_${referer}_${k}"
		println """
<edge id="${edgeId}" source="${config.schema}_${referer}" target="${config.schema}_${k}">
<data key="d2">
<y:PolyLineEdge>
<y:Path sx="0.0" sy="13.5" tx="0.0" ty="-15.0"/>
<y:LineStyle color="#000000" type="line" width="1.0"/>
<y:Arrows source="none" target="crows_foot_many_mandatory"/>
<y:EdgeLabel alignment="center" distance="2.0" fontFamily="Dialog" fontSize="12" fontStyle="plain" hasBackgroundColor="false" hasLineColor="false" height="4.0" modelName="six_pos" modelPosition="tail" preferredPlacement="anywhere" ratio="0.5" textColor="#000000" visible="true" width="4.0" x="2.0000069969042897" y="18.5"/>
<y:BendStyle smoothed="false"/>
</y:PolyLineEdge>
</data>
</edge>
"""
	}
}

println """
  <data key="d4">
    <y:Resources/>
  </data>
  </graph>
</graphml>"""
