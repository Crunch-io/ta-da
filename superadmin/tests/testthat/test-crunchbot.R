context("Crunchbot utility function")

with_mock_API({
    test_that("crunchbot", {
        expect_output(
            crunchbot(getDatasets(dsid="a2250e623c2a40d988ab7221d078034f")),
            '[{"id":"a2250e623c2a40d988ab7221d078034f","name":"YouGov/Economist Weekly Survey #235","description":"","archived":false,"project_name":"Crunch.io Devs","project_id":"80c51523fc31446396f6c915a02c77de"}]')
    })
})
