// @title KILO-AI-2API
// @version 1.0.0
// @description KILO-AI-2API
// @BasePath
package main

import (
	"fmt"
	"lmarena2api/check"
	"lmarena2api/common"
	"lmarena2api/common/config"
	logger "lmarena2api/common/loggger"
	"lmarena2api/middleware"
	"lmarena2api/model"
	"lmarena2api/router"
	"os"
	"strconv"

	"github.com/gin-gonic/gin"
)

//var buildFS embed.FS

func main() {
	logger.SetupLogger()
	logger.SysLog(fmt.Sprintf("lmarena2api %s starting...", common.Version))

	check.CheckEnvVariable()

	if os.Getenv("GIN_MODE") != "debug" {
		gin.SetMode(gin.ReleaseMode)
	}

	var err error

	model.InitTokenEncoders()

	server := gin.New()
	server.Use(gin.Recovery())
	server.Use(middleware.RequestId())
	middleware.SetUpLogger(server)

	// 设置API路由
	router.SetApiRouter(server)
	// 设置前端路由
	//router.SetWebRouter(server, buildFS)

	var port = os.Getenv("PORT")
	if port == "" {
		port = strconv.Itoa(*common.Port)
	}

	if config.DebugEnabled {
		logger.SysLog("running in DEBUG mode.")
	}

	config.InitLACookies()

	logger.SysLog("lmarena2api start success. enjoy it! ^_^\n")

	//if !config.AutoRegister {
	//go job.UpdateCookieTokenTask()
	//}
	err = server.Run(":" + port)

	if err != nil {
		logger.FatalLog("failed to start HTTP server: " + err.Error())
	}
}
