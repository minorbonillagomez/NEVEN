#+++++++++++++++++++++++++++++++++++++++++++++++++++++++
# SHARED WEBVIEW HELPERS                                +
# Canonical definition of .neven_webview_dir()          +
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++

#' Resolve NEVEN webview2-data output directory.
#'
#' Returns the path to the webview2-data directory under NEVEN_HOME,
#' creating it if it does not exist.
#'
#' @return Character string with the absolute path to the directory.
.neven_webview_dir <- function() {
  home <- Sys.getenv("NEVEN_HOME", "C:/NEVEN")
  dir <- file.path(home, "webview2-data")
  if (!dir.exists(dir)) dir.create(dir, recursive = TRUE)
  return(dir)
}
