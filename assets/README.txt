FAFE app assets — drop these image files here (exact filenames):

  support_jkopay.png   The 街口支付 (JKOPAY) logo. Shown in the Support Me
                       panel as a clickable button (fit to 260px wide, aspect
                       preserved) that opens the JKOPAY transfer link. (Was a
                       QR; replaced because the QR expired.)

  discord_logo.png     Official Discord logo (transparent PNG), used as the
                       icon on the bottom-right Discord button (~18x18).

  paypal_logo.png      Official PayPal logo/mark (transparent PNG), used as
                       the icon on the PayPal button in the Support panel
                       (~20x20).

Notes:
- Until a logo file is present, its button falls back to text only (no crash).
- Until support_jkopay.png is present, the JKOPAY button falls back to a text
  "JKOPAY" button that still opens the transfer link.
- These are bundled into the build via:  --add-data "assets;assets"
  and resolved at runtime by MainWindow._resource_path().
