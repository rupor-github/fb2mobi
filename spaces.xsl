<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" 
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
	xmlns:fb="http://www.gribuser.ru/xml/fictionbook/2.0" 
	xmlns:rupor="fb2mobi_ns" extension-element-prefixes="rupor" 
	exclude-result-prefixes="fb">

	<xsl:output method="xml" encoding="UTF-8" indent="no"/>

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>                                                                                                                                              

	<xsl:template match="fb:p[starts-with(.,'‐') or starts-with(.,'‑') or starts-with(.,'−') or starts-with(.,'–') or starts-with(.,'—') or starts-with(.,'―') or starts-with(.,'…')]">
		<rupor:katz_tr>–&#8198;</rupor:katz_tr>
	</xsl:template>

</xsl:stylesheet>