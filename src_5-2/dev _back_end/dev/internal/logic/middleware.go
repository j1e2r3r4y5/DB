package logic

import (
	"io"
	"net/http"
	"strings"

	"dev/internal/dao"
	"dev/internal/model"
	"dev/internal/service"

	"github.com/gogf/gf/v2/errors/gcode"
	"github.com/gogf/gf/v2/errors/gerror"
	"github.com/gogf/gf/v2/frame/g"
	"github.com/gogf/gf/v2/net/ghttp"
)

type sMiddleware struct {
	LoginUrl string // 登录路由地址
}

type DefaultHandlerResponse struct {
	Code    int    `json:"code"`
	Message string `json:"msg"`
	Data    any    `json:"data"`
}

func init() {
	service.RegisterMiddleware(Newmidd())
}

func Newmidd() *sMiddleware {
	return &sMiddleware{
		LoginUrl: "/loginview",
	}
}

// 流量控制
func (s *sMiddleware) RateLimitMiddleware(r *ghttp.Request) {
	tokenString := r.Header.Get("Authorization")
	ok, err := dao.Redis.Limit(r.GetCtx(), tokenString)
	if err != nil {
		g.Log().Info(r.Context(), "limit验证错误")
	}
	if !ok {
		r.Response.WriteJson(DefaultHandlerResponse{
			Code:    http.StatusTooManyRequests,
			Message: "请求过多，请稍后重试",
			Data:    r.GetHandlerResponse(),
		})
		return
	}
	r.Middleware.Next()
}

// 前台系统权限控制，用户必须登录才能访问
func (s *sMiddleware) Auth(r *ghttp.Request) {
	tokenString := r.Header.Get("Authorization")
	tokenString = strings.TrimPrefix(tokenString, "Bearer ")
	g.Log().Info(r.GetCtx(), "Auth check, tokenString:", tokenString)
	ok, err := service.Token().ValidateToken(r.Context(), tokenString)
	if err != nil {
		g.Log().Info(r.Context(), "未登录")
	}
	if ok {
		r.Middleware.Next()
	} else {
		g.Log().Info(r.GetCtx(), "go, go another land")
		r.Response.WriteJson(DefaultHandlerResponse{
			Code:    gcode.CodeInvalidRequest.Code(),
			Message: "未登录或登录过期，请重新登陆",
			Data:    "请先登录",
		})
	}
}

// 自定义上下文对象
func (s *sMiddleware) Ctx(r *ghttp.Request) {
	// 初始化，务必最开始执行
	customCtx := &model.Context{
		Data: make(g.Map),
	}
	service.Cctx().Init(r, customCtx)
	tokenString := r.Header.Get("Authorization")
	tokenString = strings.TrimPrefix(tokenString, "Bearer ")
	if userEntity, _ := service.User().GetUserInfo(r.Context(), tokenString); userEntity != nil {
		customCtx.User = &model.ContextUser{
			Id:   userEntity.Id,
			Type: userEntity.Type,
		}
		// g.Log().Info(r.GetCtx(), "用户信息已设置到上下文中", userEntity.Username)
	}
	// 将自定义的上下文对象传递到模板变量中使用
	r.Assigns(g.Map{
		"Context": customCtx,
	})
	// 执行下一步请求逻辑
	r.Middleware.Next()
}

// 跨域中间件
func (s *sMiddleware) MiddlewareCORS(r *ghttp.Request) {
	r.Response.CORSDefault()
	r.Middleware.Next()
}

// 管理权限检查
func (s *sMiddleware) AdminMiddleware(r *ghttp.Request) {
	ctx := service.Cctx().Get(r.GetCtx())
	if ctx == nil || ctx.User == nil {
		code := gcode.CodeNotAuthorized
		r.Response.WriteJson(DefaultHandlerResponse{
			Code:    code.Code(),
			Message: "未登录或用户信息异常",
			Data:    r.GetHandlerResponse(),
		})
		return
	}
	userType := ctx.User.Type
	g.Log().Debug(r.GetCtx(), "userType:", userType)
	if userType != 0 && userType != 1 {
		code := gcode.CodeNotAuthorized
		r.Response.WriteJson(DefaultHandlerResponse{
			Code:    code.Code(),
			Message: code.Message(),
			Data:    r.GetHandlerResponse(),
		})
		return
	}
	r.Middleware.Next()
}

// // 0, 3, 6, 8类用户权限检查
// func (s *sMiddleware) CheckerAndCertificaterMiddleware(r *ghttp.Request) {
// 	ok := service.User().IdentityMatch(r.GetCtx(), []int{0, 3, 6, 8})
// 	if !ok {
// 		g.Log().Debug(r.GetCtx(), "CheckerAndCertificaterMiddleware")
// 		code := gcode.CodeNotAuthorized
// 		r.Response.WriteJson(DefaultHandlerResponse{
// 			Code:    code.Code(),
// 			Message: code.Message(),
// 			Data:    r.GetHandlerResponse(),
// 		})
// 		return
// 	}
// 	r.Middleware.Next()
// }

// // 0, 1, 2, 3, 6, 7, 8类型用户权限检查
// func (s *sMiddleware) DeviceUserMiddleware(r *ghttp.Request) {
// 	ok := service.User().IdentityMatch(r.GetCtx(), []int{0, 1, 2, 3, 6, 7, 8})
// 	if !ok {
// 		code := gcode.CodeNotAuthorized
// 		r.Response.WriteJson(DefaultHandlerResponse{
// 			Code:    code.Code(),
// 			Message: code.Message(),
// 			Data:    r.GetHandlerResponse(),
// 		})
// 		return
// 	}
// 	r.Middleware.Next()
// }

// gf一般中间件，不设置则无法正确响应
func (s *sMiddleware) ResponseHandler(r *ghttp.Request) {
	// 打印请求原文

	r.Middleware.Next()
	s.PrintRequest(r)
	// 如果已经有返回内容，那么该中间件什么也不做
	if r.Response.BufferLength() > 0 {
		return
	}

	var (
		err             = r.GetError()
		res             = r.GetHandlerResponse()
		code gcode.Code = gcode.CodeOK
	)
	if err != nil {
		code = gerror.Code(err)
		g.Log().Info(r.GetCtx(), "错误信息", DefaultHandlerResponse{
			Code:    code.Code(),
			Message: err.Error(),
			Data:    res,
		})
		r.Response.WriteJson(DefaultHandlerResponse{
			Code:    code.Code(),
			Message: err.Error(),
			Data:    res,
		})
	} else {
		g.Log().Info(r.GetCtx(), "请求成功", DefaultHandlerResponse{
			Code:    code.Code(),
			Message: code.Message(),
			Data:    res,
		})
		r.Response.WriteJson(DefaultHandlerResponse{
			Code:    code.Code(),
			Message: code.Message(),
			Data:    res,
		})
	}

}

// 打印请求原文
func (s *sMiddleware) PrintRequest(r *ghttp.Request) {
	g.Log().Info(r.GetCtx(), "HTTP Method:", r.Method)
	g.Log().Info(r.GetCtx(), "Request URL:", r.URL.Path)
	// g.Log().Info(r.GetCtx(), "HTTP Headers:", r.GetHeader("Authorization"))

	body := make([]byte, r.ContentLength)
	_, err := r.Body.Read(body)
	if err != nil && err != io.EOF {
		g.Log().Debug(r.GetCtx(), "请求体读取失败", err)
	}
	g.Log().Info(r.GetCtx(), "Request Body:", string(body))
}

// // 检验外部接口开关是否开启
// func (s *sMiddleware) ExternalInterfaceSwitch(r *ghttp.Request) {
// 	Swi := service.Out().CheckSwitch(r.GetCtx())
// 	if !Swi {
// 		code := gcode.CodeInvalidOperation
// 		r.Response.WriteJson(DefaultHandlerResponse{
// 			Code:    code.Code(),
// 			Message: "外部接口未开启",
// 			Data:    r.GetHandlerResponse(),
// 		})
// 		return
// 	}
// 	r.Middleware.Next()
// }
