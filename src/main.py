from pathlib import Path

from jinja2 import Template

from config import BASE_DIR, get_previous_day, logger
from tasks import Connector

# using email friendly template

HTML_TEMPLATE = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en">
  <head>
    <!-- Compiled with Bootstrap Email version: 1.3.1 --><meta http-equiv="x-ua-compatible" content="ie=edge">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="format-detection" content="telephone=no, date=no, address=no, email=no">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta charset="UTF-8">
    <title>{{ name }} Report</title>
    <style type="text/css">
      body,table,td{font-family:Helvetica,Arial,sans-serif !important}.ExternalClass{width:100%}.ExternalClass,.ExternalClass p,.ExternalClass span,.ExternalClass font,.ExternalClass td,.ExternalClass div{line-height:150%}a{text-decoration:none}*{color:inherit}a[x-apple-data-detectors],u+#body a,#MessageViewBody a{color:inherit;text-decoration:none;font-size:inherit;font-family:inherit;font-weight:inherit;line-height:inherit}img{-ms-interpolation-mode:bicubic}table:not([class^=s-]){font-family:Helvetica,Arial,sans-serif;mso-table-lspace:0pt;mso-table-rspace:0pt;border-spacing:0px;border-collapse:collapse}table:not([class^=s-]) td{border-spacing:0px;border-collapse:collapse}@media screen and (max-width: 600px){*[class*=s-lg-]>tbody>tr>td{font-size:0 !important;line-height:0 !important;height:0 !important}}
    </style>
  </head>
  <body style="outline: 0; width: 100%; min-width: 100%; height: 100%; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-family: Helvetica, Arial, sans-serif; line-height: 24px; font-weight: normal; font-size: 16px; -moz-box-sizing: border-box; -webkit-box-sizing: border-box; box-sizing: border-box; color: #000000; margin: 0; padding: 0; border-width: 0;" bgcolor="#ffffff">
    <table class="body" valign="top" role="presentation" border="0" cellpadding="0" cellspacing="0" style="outline: 0; width: 100%; min-width: 100%; height: 100%; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-family: Helvetica, Arial, sans-serif; line-height: 24px; font-weight: normal; font-size: 16px; -moz-box-sizing: border-box; -webkit-box-sizing: border-box; box-sizing: border-box; color: #000000; border-collapse: collapse; margin: 0; padding: 0; border-width: 0;" bgcolor="#ffffff">
      <tbody>
        <tr>
          <td valign="top" style="line-height: 24px; font-size: 16px; margin: 0; padding: 8px; border: 1px solid #dddddd;" align="left">
            <h1 style="padding-top: 0; padding-bottom: 0; font-weight: 500; vertical-align: baseline; font-size: 36px; line-height: 43.2px; margin: 0;" align="left">{{ name }} - Report for {{ date }}</h1>
            <small style="font-size: 12px; line-height: 14.4px; margin: 0; padding: 0; color: #999999;">To view other days for current organization, simple change the date query in path</small>
            <table border="0" class="dataframe" cellpadding="0" cellspacing="0" style="font-family: arial, sans-serif; border-collapse: collapse; width: 100%;">
              <thead>
                <tr style="" align="right">
                  <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 8px; border: 1px solid #dddddd;" align="left"></th>
                  {% for project in columns %}
                    <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 8px; border: 1px solid #dddddd;" align="left">{{ project }}</th>
                  {% endfor %}
                </tr>
              </thead>
              <tbody>
                <tr>
                    {% for user in index %}
                    <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 8px; border: 1px solid #dddddd;" align="left">{{ user }}</th>
                        {% for item in data[loop.index0] %}
                        <td style="line-height: 24px; font-size: 16px; margin: 0; padding: 8px; border: 1px solid #dddddd;" align="left">{{ item }}</td>
                        {% endfor %}
                    {% endfor %}
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
      </tbody>
    </table>
  </body>
</html>
"""  # noqa: E501


if __name__ == "__main__":
    logger.info(f"Starting to fetch activities for {get_previous_day()}")
    result = Connector().run()

    if result:
        logger.info(f"Successfully fetched activities for {get_previous_day()}")
        for k, v in result.items():

            output_path = (
                BASE_DIR / f"html/{k}/{get_previous_day().replace('-', '')}.html"
            )
            Path.mkdir(output_path.parent, exist_ok=True)

            with open(output_path, "w+") as f:
                f.write(
                    Template(HTML_TEMPLATE).render(name=k, date=get_previous_day(), **v)
                )
            logger.info(f"Successfully saved {k} to {output_path}")
