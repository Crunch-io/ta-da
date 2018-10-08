context("HTML helpers")

df <- data.frame(v1=c("a", "z"))
expected <-
'<ul>
  <li>
    <b>a</b>
  </li>
  <li>
    <b>z</b>
  </li>
</ul>'

test_that("as.ul: <ul> from data.frame", {
    expect_output(print(
        as.ul(df, function (row) bold(row$v1))),
        expected
    )
})
test_that("as.ul doesn't add an extra li if already present", {
    expect_output(print(
        as.ul(df, function (row) li(bold(row$v1)))),
        expected
    )
})
